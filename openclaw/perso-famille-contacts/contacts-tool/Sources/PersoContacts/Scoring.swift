import Foundation

// Correspondance de noms : insensible aux accents, à la casse et à une
// transposition de lettres (« Chloé » / « Cholé »).

enum Text {
    static func fold(_ value: String) -> String {
        let folded = value.folding(
            options: [.diacriticInsensitive, .caseInsensitive, .widthInsensitive],
            locale: Locale(identifier: "fr_FR")
        )
        let mapped = folded.unicodeScalars.map { scalar -> Character in
            if CharacterSet.alphanumerics.contains(scalar) || scalar == " " { return Character(scalar) }
            return " "
        }
        return String(mapped).split(separator: " ").joined(separator: " ")
    }

    /// Damerau-Levenshtein : une transposition compte pour une seule édition.
    static func distance(_ a: String, _ b: String) -> Int {
        let lhs = Array(a), rhs = Array(b)
        if lhs.isEmpty { return rhs.count }
        if rhs.isEmpty { return lhs.count }
        var matrix = Array(repeating: Array(repeating: 0, count: rhs.count + 1), count: lhs.count + 1)
        for i in 0...lhs.count { matrix[i][0] = i }
        for j in 0...rhs.count { matrix[0][j] = j }
        for i in 1...lhs.count {
            for j in 1...rhs.count {
                let cost = lhs[i - 1] == rhs[j - 1] ? 0 : 1
                var value = min(matrix[i - 1][j] + 1, matrix[i][j - 1] + 1, matrix[i - 1][j - 1] + cost)
                if i > 1, j > 1, lhs[i - 1] == rhs[j - 2], lhs[i - 2] == rhs[j - 1] {
                    value = min(value, matrix[i - 2][j - 2] + 1)
                }
                matrix[i][j] = value
            }
        }
        return matrix[lhs.count][rhs.count]
    }

    /// Score de rapprochement ; 0 = pas de correspondance.
    static func score(needle rawNeedle: String, given rawGiven: String, family rawFamily: String) -> Int {
        let needle = fold(rawNeedle)
        guard !needle.isEmpty else { return 0 }
        let given = fold(rawGiven)
        let family = fold(rawFamily)
        let full = [given, family].filter { !$0.isEmpty }.joined(separator: " ")
        if full == needle { return 100 }
        if given == needle || family == needle { return 90 }
        if full.hasPrefix(needle) || given.hasPrefix(needle) { return 70 }
        if full.contains(needle) { return 50 }
        for token in [given, family] where !token.isEmpty {
            if distance(token, needle) <= 1 { return 40 }
        }
        return 0
    }
}

enum Projection {
    static func label(_ raw: String?) -> String {
        guard let raw, !raw.isEmpty else { return "other" }
        return raw
            .replacingOccurrences(of: "_$!<", with: "")
            .replacingOccurrences(of: ">!$_", with: "")
            .lowercased()
    }

    /// Applique la sélection de champs : les noms restent toujours présents
    /// (identification), les autres champs sont retirés s'ils ne sont pas demandés.
    static func apply(_ record: ContactRecord, fields: FieldSelection) -> ContactRecord {
        ContactRecord(
            identifier: record.identifier,
            displayName: record.displayName,
            givenName: fields.name ? record.givenName : nil,
            familyName: fields.name ? record.familyName : nil,
            organizationName: fields.name ? record.organizationName : nil,
            birthday: fields.birthday ? record.birthday : nil,
            phoneNumbers: fields.phone ? record.phoneNumbers : nil,
            emailAddresses: fields.email ? record.emailAddresses : nil,
            postalAddresses: fields.address ? record.postalAddresses : nil,
            score: record.score
        )
    }
}
