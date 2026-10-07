import SwiftUI
import iTraderCore
import AppKit

@main
struct iTraderApp: App {
    @StateObject private var appState = AppState()
    
    var body: some Scene {
        WindowGroup("iTrader") {
            RootView()
                .environmentObject(appState)
                .environment(\.dynamicTypeSize, .xLarge)
                .frame(minWidth: 880, minHeight: 580)
                .onAppear { appState.start() }
        }
        .windowResizability(.contentMinSize)

        MenuBarExtra {
            MenuBarView()
                .environmentObject(appState)
                .environment(\.dynamicTypeSize, .xLarge)
        } label: {
            Image(systemName: "gauge.with.dots.needle.bottom.50percent")
                .frame(width: 18, height: 18)
        }
        .menuBarExtraStyle(.window)
    }
}

struct RootView: View {
    @EnvironmentObject var appState: AppState
    @State private var selection = Route.workbench

    enum Route: String, CaseIterable, Identifiable {
        case workbench, live, sim, settings

        var id: String { rawValue }

        var title: String {
            switch self {
            case .workbench: return "交易工作台"
            case .live: return "实盘交易"
            case .sim: return "模拟交易"
            case .settings: return "设置"
            }
        }

        var icon: String {
            switch self {
            case .workbench: return "gauge.with.dots.needle.bottom.50percent"
            case .live: return "banknote"
            case .sim: return "testtube.2"
            case .settings: return "gearshape"
            }
        }
    }

    var body: some View {
        NavigationSplitView {
            List(selection: $selection) {
                ForEach(Route.allCases) { route in
                    NavigationLink(value: route) {
                        Label(route.title, systemImage: route.icon)
                    }
                }
            }
            .listStyle(.sidebar)
            .navigationTitle("iTrader")
        } detail: {
            VStack(spacing: 0) {
                statusBanner
                Divider()
                switch selection {
                case .workbench: WorkbenchView()
                case .live: AccountView(kind: "live")
                case .sim: SimulationView()
                case .settings: SettingsView()
                }
            }
        }
    }

    @ViewBuilder
    private var statusBanner: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(bannerColor)
                .frame(width: 9, height: 9)
            Text(bannerText)
                .font(.callout)
                .foregroundStyle(.secondary)
            Spacer()
            if !appState.backendVersion.isEmpty {
                Text("后端 v\(appState.backendVersion)")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
    }

    private var bannerColor: Color {
        switch appState.connState {
        case .connected: return .green
        case .starting: return .orange
        case .disconnected: return .red
        case .stopped: return .gray
        }
    }

    private var bannerText: String {
        switch appState.connState {
        case .connected: return "后端运行中"
        case .starting: return "正在启动后端…"
        case .disconnected: return "后端连接断开，重试中"
        case .stopped: return "后端已停止"
        }
    }
}
