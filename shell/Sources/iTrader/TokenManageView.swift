import SwiftUI

/// Token 管理页：申请、刷新并查看服务器审批状态（像素级对应 Qt TokenPage）。
struct TokenManageView: View {
    @EnvironmentObject var appState: AppState
    @Environment(\.colorScheme) private var scheme

    @State private var description = ""
    @State private var statusAlert: String?

    var body: some View {
        PageContainer {
            PageHeader(title: "Token 管理", subtitle: "申请、刷新并查看服务器审批状态。")

            AppCard {
                VStack(alignment: .leading, spacing: 12) {
                    HStack(alignment: .top, spacing: 12) {
                        Text("申请说明:")
                            .font(AppTheme.bodyFont)
                            .foregroundColor(AppTheme.ink(scheme))
                            .frame(width: 64, alignment: .trailing)
                        AppTextField(placeholder: "例如：iTrader 智能交易系统", text: $description)
                    }

                    HStack(alignment: .top, spacing: 12) {
                        Text("审批状态:")
                            .font(AppTheme.bodyFont)
                            .foregroundColor(AppTheme.ink(scheme))
                            .frame(width: 64, alignment: .trailing)
                        VStack(alignment: .leading, spacing: 6) {
                            Text(appState.tokenStatus.isEmpty ? "未申请" : appState.tokenStatus)
                                .font(AppTheme.bodyFont.weight(.semibold))
                                .foregroundColor(statusColor)
                            Text("提交申请后等待服务器审批，可通过刷新状态查看进度")
                                .font(AppTheme.dimFont)
                                .foregroundColor(AppTheme.dim(scheme))
                        }
                    }

                    HairlineDivider()

                    HStack(spacing: 10) {
                        AppButton("申请 Token", variant: .primary) { apply() }
                        AppButton("刷新状态", variant: .secondary) { appState.refreshTokenStatus() }
                        AppButton("查看状态", variant: .secondary, disabled: !approved) {
                            statusAlert = appState.tokenStatus
                        }
                        Spacer()
                    }
                }
                .padding(20)
            }
        }
        .onAppear { appState.refreshTokenStatus() }
        .alert(
            "Token 审批状态",
            isPresented: Binding(get: { statusAlert != nil }, set: { if !$0 { statusAlert = nil } }),
            presenting: statusAlert
        ) { _ in
            Button("好") {}
        } message: { status in
            Text(status)
        }
    }

    private var approved: Bool {
        appState.tokenStatus.contains("已通过")
    }

    /// 状态语义色（对应 Qt status_color：已通过绿 / 失败错误红 / 其余黄）
    private var statusColor: Color {
        let text = appState.tokenStatus
        if text.isEmpty || text == "未申请" { return AppTheme.warning(scheme) }
        if text.contains("已通过") { return AppTheme.success(scheme) }
        if text.contains("失败") || text.contains("错误") { return AppTheme.danger(scheme) }
        return AppTheme.warning(scheme)
    }

    private func apply() {
        let text = description.trimmingCharacters(in: .whitespaces)
        appState.requestToken(description: text.isEmpty ? "iTrader 智能交易系统" : text)
    }
}
