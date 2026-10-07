import SwiftUI

struct WorkbenchView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        VStack(spacing: 0) {
            Form {
                Section("自动交易") {
                    Toggle(isOn: Binding(
                        get: { appState.engineStatus.tradingActive },
                        set: { appState.toggleTrading($0) }
                    )) {
                        VStack(alignment: .leading) {
                            Text(appState.engineStatus.tradingActive ? "运行中" : "已停止")
                                .font(.headline)
                            Text("开启前会先探测服务器连通性；对所有已启用账户生效")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .disabled(appState.connState != .connected)
                    .toggleStyle(.switch)
                    .tint(appState.engineStatus.tradingActive ? .green : .gray)
                }

                Section("账户状态") {
                    if appState.engineStatus.accounts.isEmpty {
                        Text("暂无运行中的引擎。在「实盘交易」或「模拟交易」页配置并启用账户后开始。")
                            .font(.callout)
                            .foregroundStyle(.secondary)
                    }
                    ForEach(appState.engineStatus.accounts) { runtime in
                        HStack {
                            Image(systemName: runtime.running ? "play.circle.fill" : "stop.circle")
                                .foregroundStyle(runtime.running ? .green : .secondary)
                            Text(runtime.id)
                            Spacer()
                            Label(
                                runtime.serverConnected ? "服务器已连接" : "服务器未连接",
                                systemImage: runtime.serverConnected ? "wifi" : "wifi.slash"
                            )
                            .font(.caption)
                            .foregroundStyle(runtime.serverConnected ? .green : .orange)
                        }
                    }
                }

                if !appState.lastActionError.isEmpty {
                    Section {
                        Label(appState.lastActionError, systemImage: "exclamationmark.triangle")
                            .foregroundStyle(.red)
                            .font(.callout)
                    }
                }
            }
            .formStyle(.grouped)

            Divider()
            logList
        }
    }

    private var logList: some View {
        VStack(spacing: 0) {
            HStack {
                Text("日志")
                    .font(.headline)
                Spacer()
                Button("清空") { appState.logs.removeAll() }
                    .buttonStyle(.link)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 8)

            ScrollViewReader { proxy in
                List(appState.logs) { line in
                    HStack(alignment: .top, spacing: 8) {
                        Text(line.time, style: .time)
                            .font(.system(.caption, design: .monospaced))
                            .foregroundStyle(.secondary)
                            .frame(width: 64, alignment: .leading)
                        Text(line.message)
                            .font(.system(.callout, design: .monospaced))
                            .foregroundStyle(line.color)
                            .textSelection(.enabled)
                    }
                    .listRowSeparator(.hidden)
                    .id(line.id)
                }
                .listStyle(.plain)
                .onChange(of: appState.logs.count) { _ in
                    if let last = appState.logs.last {
                        proxy.scrollTo(last.id, anchor: .bottom)
                    }
                }
            }
        }
    }
}
