import Foundation

enum Output {
    static func emit<T: Codable>(_ envelope: Envelope<T>, exit code: ExitCode) -> Never {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
        if let data = try? encoder.encode(envelope), let text = String(data: data, encoding: .utf8) {
            print(text)
        } else {
            print(#"{"ok":false,"status":"unavailable","message":"encodage JSON impossible"}"#)
        }
        exit(code.rawValue)
    }

    static func success<T: Codable>(_ data: T, status: ResultStatus = .ok, message: String? = nil) -> Never {
        emit(Envelope(ok: true, status: status, message: message, data: data), exit: .ok)
    }

    static func failure<T: Codable>(_ status: ResultStatus, _ message: String, exit: ExitCode, data: T? = nil) -> Never {
        emit(Envelope(ok: false, status: status, message: message, data: data), exit: exit)
    }

    static func failure(_ status: ResultStatus, _ message: String, exit: ExitCode) -> Never {
        emit(Envelope<NoData>(ok: false, status: status, message: message, data: nil), exit: exit)
    }
}

struct NoData: Codable {}
