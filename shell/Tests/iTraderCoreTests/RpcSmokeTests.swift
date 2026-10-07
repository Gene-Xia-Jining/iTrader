import XCTest
@testable import iTraderCore

/// 真实集成冒烟：spawn Python 后端 → 握手 → 请求 → 事件 → 优雅退出。
/// workdir 用临时目录隔离，不触碰仓库 data/。
final class RpcSmokeTests: XCTestCase {
    func testConnectCallEventsQuit() async throws {
        let tempWorkdir = FileManager.default.temporaryDirectory
            .appendingPathComponent("itrader-shell-test-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: tempWorkdir, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: tempWorkdir) }

        let backend = try BackendProcess(workdirOverride: tempWorkdir)
        let info = try await backend.connectOrStart()
        XCTAssertGreaterThan(info.port, 0)
        XCTAssertFalse(info.token.isEmpty)

        final class EventCollector: @unchecked Sendable {
            var names: [String] = []
            let lock = NSLock()
            func add(_ name: String) {
                lock.lock(); names.append(name); lock.unlock()
            }
            func contains(_ name: String) -> Bool {
                lock.lock(); defer { lock.unlock() }
                return names.contains(name)
            }
        }
        let events = EventCollector()

        let client = RpcClient(info: info)
        await client.setHandlers(
            event: { name, _ in events.add(name) },
            disconnect: nil
        )
        try await client.connect()

        // app.status：全量初始状态
        let status = try await client.call(method: "app.status")
        XCTAssertFalse((status["version"] as? String ?? "").isEmpty)
        XCTAssertNotNil(status["config"])
        XCTAssertNotNil(status["engines"])

        // 双端点幂等：重复 connectOrStart 应复用同一后端（pid 一致）
        let second = try BackendProcess(workdirOverride: tempWorkdir)
        let info2 = try await second.connectOrStart()
        XCTAssertEqual(info2.pid, info.pid)

        // config.save（空参数=沿用现值）应推送 config_changed + log 事件
        let saveResp = try await client.call(method: "config.save", params: [:])
        XCTAssertTrue(saveResp.isEmpty)
        try await Task.sleep(nanoseconds: 800_000_000)
        XCTAssertTrue(events.contains("config_changed"), "实际事件: \(events.names)")
        XCTAssertTrue(events.contains("log"), "实际事件: \(events.names)")

        // app.quit：优雅退出（asyncio 收尾 + 进程退出有耗时，轮询等待）
        _ = try await client.call(method: "app.quit")
        let deadline = Date().addingTimeInterval(5)
        while Date() < deadline && BackendProcess.isPidAlive(info.pid) {
            try await Task.sleep(nanoseconds: 200_000_000)
        }
        backend.terminate()  // 兜底，正常路径应已退出
        XCTAssertFalse(BackendProcess.isPidAlive(info.pid), "后端应已退出")
    }
}
