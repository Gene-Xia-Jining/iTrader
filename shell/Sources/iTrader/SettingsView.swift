import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var appState: AppState
    @State private var serverUrl = ""
    @State private var proxyUrl = ""
    @State private var serverTestResult = ""
    @State private var tokenDescription = ""

    var body: some View {
        Form {
            serverSection
            tokenSection
            updateSection
            backendSection
        }
        .formStyle(.grouped)
        .onAppear {
            serverUrl = appState.config.serverUrl
            proxyUrl = appState.config.proxyUrl
            appState.refreshTokenStatus()
        }
    }

    // MARK: 服务器连接

    private var serverSection: some View {
        Section("服务器连接") {
            TextField("服务器地址", text: $serverUrl, prompt: Text("http://192.168.100.100:3080"))
            TextField("代理地址（留空 = 强制直连）", text: $proxyUrl)
            HStack {
                Button("测试连接") {
                    Task {
                        serverTestResult = "测试中…"
                        serverTestResult = await appState.testServer(url: serverUrl)
                    }
                }
                Button("保存") {
                    appState.saveConfig(
                        serverUrl: serverUrl.isEmpty ? nil : serverUrl,
                        proxyUrl: proxyUrl.isEmpty ? "" : proxyUrl
                    )
                }
                .buttonStyle(.borderedProminent)
                if !serverTestResult.isEmpty {
                    Text(serverTestResult)
                        .font(.caption)
                        .foregroundStyle(serverTestResult.contains("成功") ? .green : .red)
                }
            }
        }
    }

    // MARK: 访问 Token

    private var tokenSection: some View {
        Section("服务器访问 Token") {
            HStack {
                Text(appState.tokenStatus.isEmpty ? "未查询" : appState.tokenStatus)
                    .font(.callout)
                    .foregroundStyle(.secondary)
                Spacer()
                Button("刷新状态") { appState.refreshTokenStatus() }
            }
            HStack {
                TextField("申请描述（可选）", text: $tokenDescription)
                Button("申请 Token") {
                    appState.requestToken(description: tokenDescription)
                    tokenDescription = ""
                }
            }
        }
    }

    // MARK: 自动更新

    private var updateSection: some View {
        Section("软件更新（当前 v\(appState.backendVersion)）") {
            HStack {
                Button("检查更新") { appState.checkUpdate() }
                    .disabled(appState.updatePhase == .checking || appState.updatePhase == .downloading)
                if appState.updatePhase == .downloading {
                    Button("取消下载") { appState.cancelUpdate() }
                }
                if case .available(let version, let hasPatch) = appState.updatePhase {
                    Button("下载 v\(version)\(hasPatch ? "（差量）" : "")") { appState.downloadUpdate() }
                        .buttonStyle(.borderedProminent)
                }
                if case .ready(let kind) = appState.updatePhase {
                    Button("安装并重启后端（\(kind)）") { appState.applyUpdate() }
                        .buttonStyle(.borderedProminent)
                }
            }
            phaseDescription
        }
    }

    @ViewBuilder
    private var phaseDescription: some View {
        switch appState.updatePhase {
        case .checking:
            Label("正在检查更新…", systemImage: "arrow.triangle.2.circlepath").font(.caption).foregroundStyle(.secondary)
        case .downloading:
            Label("正在下载更新…", systemImage: "arrow.down.circle").font(.caption).foregroundStyle(.secondary)
        case .latest(let msg):
            Label(msg, systemImage: "checkmark.circle").font(.caption).foregroundStyle(.green)
        case .failed(let msg):
            Label(msg, systemImage: "exclamationmark.triangle").font(.caption).foregroundStyle(.red)
        default:
            EmptyView()
        }
    }

    // MARK: 后端控制

    private var backendSection: some View {
        Section("后端进程") {
            HStack {
                Button("退出后端", role: .destructive) { appState.quitBackend() }
                    .disabled(appState.connState != .connected)
                Text("退出后自动交易停止；壳进程会尝试重新拉起")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }
}
