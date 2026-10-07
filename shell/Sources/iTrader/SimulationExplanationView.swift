import SwiftUI

struct SimulationExplanationView: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("在开始实盘交易之前，您应该通过 1-3 个月的模拟交易建立信心。\n\n我们支持快期的模拟交易，您需要：")
                .font(.callout)
                .foregroundColor(.secondary)
            
            Text("1，下载快期模拟版客户端：")
                .font(.callout)
                .foregroundColor(.primary)
            
            Link("手机端：", destination: URL(string: "https://www.shinnytech.com/products/app")!)
                .font(.callout)
                .foregroundColor(.blue)
            
            Link("App Store：", destination: URL(string: "https://itunes.apple.com/us/app/快期小q/id1187762307?l=zh&ls=1&mt=8")!)
                .font(.callout)
                .foregroundColor(.blue)
            
            Link("Windows：", destination: URL(string: "https://www.shinnytech.com/products/q73")!)
                .font(.callout)
                .foregroundColor(.blue)
            
            Divider()
            
            Text("2，在快期客户端或天勤官网注册：")
                .font(.callout)
                .foregroundColor(.primary)
            
            Link("天勤官网：", destination: URL(string: "https://account.shinnytech.com/")!)
                .font(.callout)
                .foregroundColor(.blue)
            
            Divider()
            
            Text("3，在这里填入：")
                .font(.callout)
                .foregroundColor(.primary)
        }
        .padding()
        .background(Color(NSColor.windowBackgroundColor))
        .cornerRadius(8)
    }
}