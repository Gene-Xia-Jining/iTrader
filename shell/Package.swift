// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "iTrader",
    platforms: [.macOS(.v13)],
    targets: [
        // 无 UI 核心层：后端进程管理 + RPC 客户端（可单元测试）
        .target(name: "iTraderCore"),
        // SwiftUI 壳
        .executableTarget(
            name: "iTrader",
            dependencies: ["iTraderCore"]
        ),
        .testTarget(
            name: "iTraderCoreTests",
            dependencies: ["iTraderCore"]
        ),
    ]
)
