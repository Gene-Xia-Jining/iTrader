import SwiftUI

/// 期货公司分组（与 Qt 版 BROKER_GROUPS 保持一致）
let BROKER_GROUPS: [(group: String, brokers: [String])] = [
    ("天勤免费版", ["宏源期货", "徽商期货", "银河期货"]),
    ("天勤专业版", ["东方汇金", "光大期货", "国泰君安"]),
]

struct AccountView: View {
    let kind: String
    @EnvironmentObject var appState: AppState
    @State private var addingNew = false

    private var kindAccounts: [AccountInfo] {
        appState.accounts.filter { $0.kind == kind }
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                if kind == "sim" {
                    // 快期模拟账户全局仅一个
                    if let sim = kindAccounts.first {
                        AccountCard(account: sim)
                    } else {
                        AccountCard(account: nil)
                    }
                } else {
                    ForEach(kindAccounts) { account in
                        AccountCard(account: account)
                    }
                    if addingNew {
                        AccountCard(account: nil)
                    } else {
                        Button {
                            addingNew = true
                        } label: {
                            Label("新增实盘账户", systemImage: "plus")
                        }
                        .buttonStyle(.borderless)
                        .opacity(kindAccounts.isEmpty ? 1 : 0.8)
                    }
                }
            }
            .padding(20)
        }
        .background(Color(nsColor: .windowBackgroundColor).opacity(0.4))
    }
}

/// 单个账户卡片：nil = 新建表单
private struct AccountCard: View {
    let account: AccountInfo?
    @EnvironmentObject var appState: AppState

    var body: some View {
        AccountFormView(kind: account?.kind ?? "live", account: account)
    }
}

// MARK: - 账户表单

private struct AccountFormView: View {
    let kind: String
    let account: AccountInfo?
    @EnvironmentObject var appState: AppState
    @Environment(\.dismiss) private var dismiss

    @State private var label = ""
    @State private var tqAccount = ""
    @State private var tqPassword = ""
    @State private var broker = ""
    @State private var tradeAccount = ""
    @State private var tradePassword = ""
    @State private var enabled = true
    @State private var selectedSymbols: Set<String> = []
    @State private var manualSymbol = ""
    @State private var testResult = ""
    @State private var saveMessage = ""
    @State private var expanded = false

    var body: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 14) {
                header
                if expanded || account == nil {
                    fields
                    symbolSection
                    actionButtons
                }
                if !testResult.isEmpty {
                    Text(testResult)
                        .font(.caption)
                        .foregroundStyle(testResult.contains("成功") ? .green : .red)
                }
                if !saveMessage.isEmpty {
                    Text(saveMessage)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(6)
        } label: {
            Label(title, systemImage: kind == "sim" ? "testtube.2" : "banknote")
        }
        .onAppear(perform: fillFromAccount)
    }

    private var title: String {
        if let account {
            return "\(account.label)（\(account.id)）"
        }
        return kind == "sim" ? "快期模拟账户（尚未配置）" : "新实盘账户"
    }

    private var header: some View {
        HStack {
            Text(title).font(.headline)
            if let account {
                Spacer()
                Toggle("启用", isOn: $enabled)
                    .toggleStyle(.switch)
                    .controlSize(.small)
                Button(expanded ? "收起" : "编辑") { expanded.toggle() }
                    .buttonStyle(.link)
            }
        }
    }

    private var fields: some View {
        Form {
            TextField("显示名称", text: $label, prompt: Text(kind == "sim" ? "模拟账户" : "实盘账户"))
            TextField("快期账户（TqAuth）", text: $tqAccount, prompt: Text("快期账号/手机号"))
            SecureField("快期密码", text: $tqPassword, prompt: Text(account == nil ? "必填" : "留空 = 不修改"))

            if kind == "live" {
                Picker("期货公司", selection: $broker) {
                    Text("未选择").tag("")
                    ForEach(BROKER_GROUPS, id: \.group) { group in
                        Section(group.group) {
                            ForEach(group.brokers, id: \.self) { name in
                                Text(name).tag(name)
                            }
                        }
                    }
                }
                TextField("资金账号", text: $tradeAccount)
                SecureField("交易密码", text: $tradePassword, prompt: Text(account == nil ? "必填" : "留空 = 不修改"))
            }

            HStack {
                Button("测试快期账户") {
                    Task {
                        testResult = "测试中…"
                        testResult = await appState.testTqAuth(account: tqAccount, password: tqPassword)
                    }
                }
                .disabled(tqAccount.isEmpty || tqPassword.isEmpty)
                Button("测试服务器") {
                    Task {
                        testResult = "测试中…"
                        testResult = await appState.testServer(url: nil)
                    }
                }
            }
        }
        .formStyle(.grouped)
    }

    private var symbolSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("订阅品种").font(.subheadline.weight(.medium))
                Spacer()
                Button("从服务器获取") { appState.fetchSymbols() }
                    .buttonStyle(.link)
            }
            if !appState.symbolsMessage.isEmpty {
                Text(appState.symbolsMessage)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            if appState.serverSymbols.isEmpty {
                Text("先在设置页配置服务器地址，获取品种列表后勾选；也可手动输入品种代码（如 SHFE.cu2501）")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            } else {
                FlowGrid(items: appState.serverSymbols.sorted(), selected: $selectedSymbols)
            }
            HStack {
                TextField("手动添加品种", text: $manualSymbol)
                    .textFieldStyle(.roundedBorder)
                    .onSubmit(addManualSymbol)
                Button("添加") { addManualSymbol() }
            }
            if !selectedSymbols.isEmpty {
                Text("已选 \(selectedSymbols.count) 个：\(selectedSymbols.sorted().joined(separator: ", "))")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 4)
    }

    private func addManualSymbol() {
        let symbol = manualSymbol.trimmingCharacters(in: .whitespaces)
        guard !symbol.isEmpty else { return }
        selectedSymbols.insert(symbol)
        manualSymbol = ""
    }

    private var actionButtons: some View {
        HStack {
            Button("保存") { save() }
                .buttonStyle(.borderedProminent)
            if let account {
                Button("删除账户", role: .destructive) {
                    Task {
                        await appState.runAction(method: "accounts.delete", params: ["account_id": account.id])
                        saveMessage = "已删除"
                    }
                }
            }
            Spacer()
        }
    }

    private func fillFromAccount() {
        guard let account else { return }
        label = account.label
        tqAccount = account.tqAccount
        broker = account.broker
        tradeAccount = account.tradeAccount
        enabled = account.enabled
        selectedSymbols = Set(account.symbols)
    }

    private func save() {
        var params: [String: Any] = [
            "kind": kind,
            "label": label,
            "tq_account": tqAccount,
            "symbols": Array(selectedSymbols),
            "enabled": enabled,
        ]
        if let account { params["account_id"] = account.id }
        if !tqPassword.isEmpty { params["tq_password"] = tqPassword }
        if kind == "live" {
            params["broker"] = broker
            params["trade_account"] = tradeAccount
            if !tradePassword.isEmpty { params["trade_password"] = tradePassword }
        }
        Task {
            await appState.runAction(method: "accounts.save", params: params)
            saveMessage = "已保存（引擎运行中则下次启动生效）"
            if account == nil { expanded = false }
        }
    }
}

// MARK: - 品种多选网格

struct FlowGrid: View {
    let items: [String]
    @Binding var selected: Set<String>

    var body: some View {
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 150), spacing: 6)], alignment: .leading, spacing: 6) {
            ForEach(items, id: \.self) { symbol in
                Toggle(isOn: Binding(
                    get: { selected.contains(symbol) },
                    set: { if $0 { selected.insert(symbol) } else { selected.remove(symbol) } }
                )) {
                    Text(symbol)
                        .font(.callout)
                        .lineLimit(1)
                }
                .toggleStyle(.checkbox)
            }
        }
    }
}
