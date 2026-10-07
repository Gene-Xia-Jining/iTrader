import Foundation

/// data/backend.json 的内容：后端启动后写入，壳据此连接。
public struct BackendInfo: Codable {
    public let port: Int
    public let token: String
    public let pid: Int
    public let version: String
}

/// 后端进程管理：定位启动命令、spawn、等待发现文件、健康检查、终止。
///
/// 布局探测（两者取其一）：
/// - bundle 态：Resources/backend_root.txt 内容为业务根目录路径（build_shell.sh 生成）；
/// - 开发态：从本文件编译位置向上查找 src/backend/__main__.py 所在仓库根。
/// 业务根目录须同时包含 .venv/bin/python 与 src/（与现有开发/打包布局一致）。
public final class BackendProcess {
    public enum BackendError: LocalizedError, Sendable {
        case layoutNotFound
        case pythonMissing(String)
        case infoTimeout(String)
        case alreadyRunning

        public var errorDescription: String? {
            switch self {
            case .layoutNotFound:
                return "未找到后端业务根目录（需要 .venv 与 src/backend）"
            case .pythonMissing(let path):
                return "未找到 Python 解释器: \(path)"
            case .infoTimeout(let path):
                return "等待 \(path) 超时，后端可能启动失败"
            case .alreadyRunning:
                return "后端已在运行"
            }
        }
    }

    let repoRoot: URL
    private let workdirOverride: URL?
    private var process: Process?
    private(set) var info: BackendInfo?

    public var workdir: URL { workdirOverride ?? repoRoot }
    public var infoURL: URL { workdir.appendingPathComponent("data/backend.json") }

    /// 崩溃/退出回调（主线程外触发）
    public var onExit: (() -> Void)?

    /// workdirOverride：测试用临时目录隔离 data/；生产环境用默认（= repoRoot）
    public init(repoRootOverride: URL? = nil, workdirOverride: URL? = nil) throws {
        self.repoRoot = try repoRootOverride ?? Self.detectRepoRoot()
        self.workdirOverride = workdirOverride
        let python = Self.pythonURL(repoRoot: self.repoRoot)
        guard FileManager.default.fileExists(atPath: python.path) else {
            throw BackendError.pythonMissing(python.path)
        }
    }

    /// 已有后端在运行（backend.json 中 pid 存活）时直接复用，不 spawn 新进程。
    public func connectOrStart() async throws -> BackendInfo {
        if let existing = Self.readInfo(from: infoURL), Self.isPidAlive(existing.pid) {
            info = existing
            return existing
        }
        return try await start()
    }

    public func start() async throws -> BackendInfo {
        guard process == nil else { throw BackendError.alreadyRunning }
        try? FileManager.default.removeItem(at: infoURL)

        let proc = Process()
        proc.executableURL = Self.pythonURL(repoRoot: repoRoot)
        proc.arguments = ["-m", "src.backend"]
        proc.currentDirectoryURL = workdir
        var env = ProcessInfo.processInfo.environment
        env["PYTHONPATH"] = repoRoot.path
        proc.environment = env
        // 后端日志默认丢弃（发现文件是主通道）；调 ITRADER_BACKEND_VERBOSE=1 时继承输出便于排障
        if ProcessInfo.processInfo.environment["ITRADER_BACKEND_VERBOSE"] == nil {
            proc.standardOutput = FileHandle.nullDevice
            proc.standardError = FileHandle.nullDevice
        }
        proc.terminationHandler = { [weak self] _ in
            self?.process = nil
            self?.onExit?()
        }
        try proc.run()
        process = proc

        guard let found = await waitForInfo(timeout: 15) else {
            throw BackendError.infoTimeout(infoURL.path)
        }
        info = found
        return found
    }

    public func terminate() {
        guard let proc = process, proc.isRunning else { return }
        proc.interrupt()  // SIGINT：后端按优雅退出路径释放 TqApi 连接
        let deadline = Date().addingTimeInterval(3)
        while proc.isRunning && Date() < deadline {
            Thread.sleep(forTimeInterval: 0.05)
        }
        if proc.isRunning { proc.terminate() }
    }

    // -------- helpers --------

    private func waitForInfo(timeout: TimeInterval) async -> BackendInfo? {
        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            if let info = Self.readInfo(from: infoURL) { return info }
            try? await Task.sleep(nanoseconds: 200_000_000)
        }
        return nil
    }

    public static func readInfo(from url: URL) -> BackendInfo? {
        guard let data = try? Data(contentsOf: url),
              let info = try? JSONDecoder().decode(BackendInfo.self, from: data)
        else { return nil }
        return info
    }

    public static func isPidAlive(_ pid: Int) -> Bool {
        kill(pid_t(pid), 0) == 0
    }

    private static func pythonURL(repoRoot: URL) -> URL {
        if let override = ProcessInfo.processInfo.environment["ITRADER_PYTHON"] {
            return URL(fileURLWithPath: override)
        }
        return repoRoot.appendingPathComponent(".venv/bin/python")
    }

    private static func detectRepoRoot() throws -> URL {
        // bundle 态：build_shell.sh 在 Resources 里放置业务根路径
        let marker = Bundle.main.url(forResource: "backend_root", withExtension: "txt")
        if let marker, let root = try? String(contentsOf: marker, encoding: .utf8) {
            let url = URL(fileURLWithPath: root.trimmingCharacters(in: .whitespacesAndNewlines))
            if FileManager.default.fileExists(atPath: url.appendingPathComponent("src/backend/__main__.py").path) {
                return url
            }
        }
        // 开发态：从源码位置向上找
        var dir = URL(fileURLWithPath: (#filePath as NSString).deletingLastPathComponent)
        for _ in 0..<8 {
            if FileManager.default.fileExists(atPath: dir.appendingPathComponent("src/backend/__main__.py").path) {
                return dir
            }
            dir.deleteLastPathComponent()
        }
        throw BackendError.layoutNotFound
    }
}
