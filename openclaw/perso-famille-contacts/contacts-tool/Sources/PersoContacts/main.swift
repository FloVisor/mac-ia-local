import Contacts
import Foundation

// perso-contacts — lecture seule du carnet iCloud via CNContactStore.
// Aucune écriture, aucun cache persistant, aucun export complet.

struct Arguments {
    var command: String = ""
    var query: String?
    var identifier: String?
    var container: String?
    var fields: FieldSelection = .all
    var limit: Int = 10
    var fuzzy = false
}

func parseArguments(_ argv: [String]) -> Arguments {
    var args = Arguments()
    var index = 1
    if argv.count > 1, !argv[1].hasPrefix("-") {
        args.command = argv[1]
        index = 2
    }
    while index < argv.count {
        let token = argv[index]
        func next() -> String? {
            guard index + 1 < argv.count else { return nil }
            index += 1
            return argv[index]
        }
        switch token {
        case "--query", "-q": args.query = next()
        case "--id": args.identifier = next()
        case "--container": args.container = next()
        case "--limit", "-n": args.limit = Int(next() ?? "") ?? args.limit
        case "--fuzzy": args.fuzzy = true
        case "--fields":
            guard let raw = next(), let parsed = FieldSelection.parse(raw) else {
                Output.failure(.invalidArgument, "champ inconnu dans --fields (name,birthday,phone,email,address)", exit: .invalidArgument)
            }
            args.fields = parsed
        case "--help", "-h":
            print(usage)
            exit(0)
        default:
            Output.failure(.invalidArgument, "option inconnue: \(token)", exit: .invalidArgument)
        }
        index += 1
    }
    return args
}

let usage = """
perso-contacts — lecture seule du carnet iCloud (CNContactStore)

  perso-contacts status [--json]
  perso-contacts containers
  perso-contacts search --query <texte> [--limit N] [--fuzzy] [--fields ...] [--container <id|nom>]
  perso-contacts get --id <CNContact.identifier> [--fields ...] [--container <id|nom>]
  perso-contacts request-access

Sortie JSON: { ok, status, message, data }.
status ∈ ok | not_found | ambiguous | denied | not_determined | unavailable | invalid_argument | invalid_id
"""

let args = parseArguments(CommandLine.arguments)
let store = ContactsStore()

func containerInfo(_ container: CNContainer?) -> ContainerInfo? {
    container.map(ContactsStore.describe)
}

func handleError(_ error: Error) -> Never {
    switch error {
    case ContactsError.denied:
        Output.failure(.denied, "accès Contacts refusé (Réglages Système → Confidentialité → Contacts)", exit: .denied)
    case ContactsError.notDetermined:
        Output.failure(.notDetermined, "autorisation Contacts non accordée: lancer `perso-contacts request-access`", exit: .denied)
    case ContactsError.unavailable(let message):
        Output.failure(.unavailable, message, exit: .unavailable)
    case ContactsError.invalidArgument(let message):
        Output.failure(.invalidArgument, message, exit: .invalidArgument)
    default:
        Output.failure(.unavailable, "erreur Contacts: \(error.localizedDescription)", exit: .unavailable)
    }
}

switch args.command {
case "status":
    let status = store.authorizationStatus()
    let name: String
    switch status {
    case .authorized: name = "authorized"
    case .denied: name = "denied"
    case .restricted: name = "restricted"
    case .notDetermined: name = "not_determined"
    @unknown default: name = "unknown"
    }
    var containers: [ContainerInfo] = []
    var selected: ContainerInfo?
    if status == .authorized {
        do {
            containers = try store.containers().map(ContactsStore.describe)
            selected = containerInfo(try? store.selectContainer(explicit: args.container))
        } catch {
            handleError(error)
        }
    }
    Output.success(StatusData(authorization: name, containers: containers, selectedContainer: selected))

case "containers":
    do {
        try store.requireAccess()
        let containers = try store.containers().map(ContactsStore.describe)
        let selected = containerInfo(try? store.selectContainer(explicit: args.container))
        Output.success(ContainersData(containers: containers, selectedContainer: selected))
    } catch {
        handleError(error)
    }

case "request-access":
    if store.authorizationStatus() == .authorized {
        Output.success(StatusData(authorization: "authorized", containers: [], selectedContainer: nil), message: "déjà autorisé")
    }
    let granted = store.requestAccess()
    if granted {
        Output.success(StatusData(authorization: "authorized", containers: [], selectedContainer: nil))
    }
    Output.failure(.denied, "autorisation refusée", exit: .denied)

case "search":
    guard let query = args.query, !query.trimmingCharacters(in: .whitespaces).isEmpty else {
        Output.failure(.invalidArgument, "--query requis", exit: .invalidArgument)
    }
    do {
        try store.requireAccess()
        let container = try store.selectContainer(explicit: args.container)
        let limit = max(1, min(args.limit, 25))
        var scored: [(CNContact, Int)] = try store.search(query: query, container: container, fields: args.fields, limit: limit)
            .map { ($0, 0) }
        if scored.isEmpty, args.fuzzy {
            scored = try store.searchFuzzy(query: query, container: container, fields: args.fields, limit: limit)
        }
        let records = scored.map { Projection.record($0.0, fields: args.fields, score: $0.1 == 0 ? nil : $0.1) }
        let data = SearchData(
            query: query,
            container: ContactsStore.describe(container),
            candidates: records,
            ambiguous: records.count > 1,
            truncated: records.count >= limit
        )
        if records.isEmpty {
            Output.failure(.notFound, "aucune fiche pour « \(query) » dans le carnet \(container.name)", exit: .notFound, data: data)
        }
        Output.success(data, status: records.count > 1 ? .ambiguous : .ok)
    } catch {
        handleError(error)
    }

case "get":
    guard let identifier = args.identifier, !identifier.isEmpty else {
        Output.failure(.invalidArgument, "--id requis", exit: .invalidArgument)
    }
    do {
        try store.requireAccess()
        let container = try store.selectContainer(explicit: args.container)
        guard let contact = try store.fetch(identifier: identifier, container: container, fields: args.fields) else {
            Output.failure(.invalidId, "identifiant absent du carnet \(container.name): \(identifier)", exit: .notFound)
        }
        Output.success(GetData(container: ContactsStore.describe(container), contact: Projection.record(contact, fields: args.fields)))
    } catch {
        handleError(error)
    }

default:
    print(usage)
    exit(args.command.isEmpty ? 0 : Int32(ExitCode.invalidArgument.rawValue))
}
