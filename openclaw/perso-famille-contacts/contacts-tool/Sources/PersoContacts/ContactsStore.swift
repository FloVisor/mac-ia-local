import Contacts
import Foundation

enum ContactsError: Error {
    case denied
    case notDetermined
    case unavailable(String)
    case invalidArgument(String)
}

struct ContactsStore {
    let store = CNContactStore()

    // MARK: - Autorisation

    func authorizationStatus() -> CNAuthorizationStatus {
        CNContactStore.authorizationStatus(for: .contacts)
    }

    /// Demande explicite uniquement : jamais déclenchée implicitement par une recherche.
    func requestAccess() -> Bool {
        var granted = false
        let semaphore = DispatchSemaphore(value: 0)
        store.requestAccess(for: .contacts) { ok, _ in
            granted = ok
            semaphore.signal()
        }
        semaphore.wait()
        return granted
    }

    func requireAccess() throws {
        switch authorizationStatus() {
        case .authorized:
            return
        case .denied, .restricted:
            throw ContactsError.denied
        case .notDetermined:
            throw ContactsError.notDetermined
        @unknown default:
            throw ContactsError.unavailable("statut d'autorisation inconnu")
        }
    }

    // MARK: - Conteneurs

    func containers() throws -> [CNContainer] {
        try store.containers(matching: nil)
    }

    static func describe(_ container: CNContainer) -> ContainerInfo {
        let type: String
        switch container.type {
        case .local: type = "local"
        case .exchange: type = "exchange"
        case .cardDAV: type = "carddav"
        case .unassigned: type = "unassigned"
        @unknown default: type = "unknown"
        }
        return ContainerInfo(identifier: container.identifier, name: container.name, type: type)
    }

    /// Sélectionne le carnet iCloud sans inclure silencieusement un carnet
    /// professionnel ou un autre compte présent sur le Mac.
    func selectContainer(explicit: String?) throws -> CNContainer {
        let all = try containers()
        guard !all.isEmpty else {
            throw ContactsError.unavailable("aucun carnet de contacts accessible")
        }
        if let explicit, !explicit.isEmpty {
            let matches = all.filter {
                $0.identifier == explicit || $0.name.caseInsensitiveCompare(explicit) == .orderedSame
            }
            if matches.count == 1 { return matches[0] }
            if matches.isEmpty { throw ContactsError.invalidArgument("carnet introuvable: \(explicit)") }
            throw ContactsError.invalidArgument("carnet ambigu: \(explicit)")
        }
        let icloud = all.filter { $0.name.range(of: "icloud", options: .caseInsensitive) != nil }
        if icloud.count == 1 { return icloud[0] }
        if icloud.count > 1 { throw ContactsError.invalidArgument("plusieurs carnets iCloud: préciser --container") }
        if all.count == 1 { return all[0] }
        throw ContactsError.invalidArgument("aucun carnet iCloud identifié: préciser --container")
    }

    // MARK: - Lecture

    func fetch(identifier: String, container: CNContainer, fields: FieldSelection) throws -> CNContact? {
        let predicate = CNContact.predicateForContactsInContainer(withIdentifier: container.identifier)
        let matches = try store.unifiedContacts(matching: predicate, keysToFetch: fields.keys)
        return matches.first { $0.identifier == identifier }
    }

    /// Recherche native (index Contacts) bornée au carnet ciblé.
    func search(query: String, container: CNContainer, fields: FieldSelection, limit: Int) throws -> [CNContact] {
        let containerPredicate = CNContact.predicateForContactsInContainer(withIdentifier: container.identifier)
        let namePredicate = CNContact.predicateForContacts(matchingName: query)
        let predicate = NSCompoundPredicate(andPredicateWithSubpredicates: [containerPredicate, namePredicate])
        let matches = try store.unifiedContacts(matching: predicate, keysToFetch: fields.keys)
        return Array(matches.prefix(limit))
    }

    /// Repli tolérant (accents, transposition) : parcourt les noms du seul carnet ciblé.
    func searchFuzzy(query: String, container: CNContainer, fields: FieldSelection, limit: Int) throws -> [(CNContact, Int)] {
        let predicate = CNContact.predicateForContactsInContainer(withIdentifier: container.identifier)
        let matches = try store.unifiedContacts(matching: predicate, keysToFetch: fields.keys)
        var scored: [(CNContact, Int)] = []
        for contact in matches {
            let score = Text.score(needle: query, given: contact.givenName, family: contact.familyName)
            if score > 0 { scored.append((contact, score)) }
        }
        scored.sort { $0.1 > $1.1 }
        return Array(scored.prefix(limit))
    }
}

// MARK: - Projection

extension Projection {
    static func record(_ contact: CNContact, fields: FieldSelection, score: Int? = nil) -> ContactRecord {
        // Ne jamais lire une propriété non demandée : CNContact lève une exception.
        var birthday: Birthday?
        if fields.birthday, let components = contact.birthday {
            birthday = Birthday(year: components.year, month: components.month, day: components.day)
        }
        let phones = !fields.phone || contact.phoneNumbers.isEmpty ? nil : contact.phoneNumbers.map {
            LabeledValue(label: label($0.label), value: $0.value.stringValue)
        }
        let emails = !fields.email || contact.emailAddresses.isEmpty ? nil : contact.emailAddresses.map {
            LabeledValue(label: label($0.label), value: $0.value as String)
        }
        let addresses = !fields.address || contact.postalAddresses.isEmpty ? nil : contact.postalAddresses.map { entry in
            let value = entry.value
            return PostalAddress(
                label: label(entry.label),
                street: value.street.isEmpty ? nil : value.street,
                city: value.city.isEmpty ? nil : value.city,
                postalCode: value.postalCode.isEmpty ? nil : value.postalCode,
                country: value.country.isEmpty ? nil : value.country
            )
        }
        let display = [contact.givenName, contact.familyName]
            .filter { !$0.isEmpty }
            .joined(separator: " ")
        let record = ContactRecord(
            identifier: contact.identifier,
            displayName: display.isEmpty ? contact.organizationName : display,
            givenName: contact.givenName.isEmpty ? nil : contact.givenName,
            familyName: contact.familyName.isEmpty ? nil : contact.familyName,
            organizationName: contact.organizationName.isEmpty ? nil : contact.organizationName,
            birthday: birthday,
            phoneNumbers: phones,
            emailAddresses: emails,
            postalAddresses: addresses,
            score: score
        )
        return apply(record, fields: fields)
    }
}
