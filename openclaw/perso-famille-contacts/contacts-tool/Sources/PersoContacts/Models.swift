import Contacts
import Foundation

/// Statuts de sortie normalisés. Un appelant doit pouvoir distinguer
/// « pas de fiche », « champ absent », « ambiguïté » et « autorisation refusée ».
enum ResultStatus: String, Codable {
    case ok
    case notFound = "not_found"
    case ambiguous
    case denied
    case notDetermined = "not_determined"
    case unavailable
    case invalidArgument = "invalid_argument"
    case invalidId = "invalid_id"
}

enum ExitCode: Int32 {
    case ok = 0
    case notFound = 2
    case ambiguous = 3
    case denied = 4
    case unavailable = 5
    case invalidArgument = 6
}

struct Birthday: Codable {
    let year: Int?
    let month: Int?
    let day: Int?
}

struct LabeledValue: Codable {
    let label: String
    let value: String
}

struct PostalAddress: Codable {
    let label: String
    let street: String?
    let city: String?
    let postalCode: String?
    let country: String?
}

struct ContactRecord: Codable {
    let identifier: String
    let displayName: String
    let givenName: String?
    let familyName: String?
    let organizationName: String?
    let birthday: Birthday?
    let phoneNumbers: [LabeledValue]?
    let emailAddresses: [LabeledValue]?
    let postalAddresses: [PostalAddress]?
    let score: Int?
}

struct ContainerInfo: Codable {
    let identifier: String
    let name: String
    let type: String
}

struct Envelope<T: Codable>: Codable {
    let ok: Bool
    let status: ResultStatus
    let message: String?
    let data: T?
}

struct SearchData: Codable {
    let query: String
    let container: ContainerInfo
    let candidates: [ContactRecord]
    let ambiguous: Bool
    let truncated: Bool
}

struct GetData: Codable {
    let container: ContainerInfo?
    let contact: ContactRecord
}

struct StatusData: Codable {
    let authorization: String
    let containers: [ContainerInfo]
    let selectedContainer: ContainerInfo?
}

struct ContainersData: Codable {
    let containers: [ContainerInfo]
    let selectedContainer: ContainerInfo?
}

/// Champs demandés par l'appelant : on ne lit jamais plus que nécessaire.
struct FieldSelection {
    var name = true
    var birthday = true
    var phone = true
    var email = true
    var address = true

    static let all = FieldSelection()

    static func parse(_ raw: String) -> FieldSelection? {
        var selection = FieldSelection(name: false, birthday: false, phone: false, email: false, address: false)
        for token in raw.split(separator: ",") {
            switch token.trimmingCharacters(in: .whitespaces).lowercased() {
            case "name", "nom": selection.name = true
            case "birthday", "anniversaire": selection.birthday = true
            case "phone", "telephone", "téléphone": selection.phone = true
            case "email", "mail": selection.email = true
            case "address", "adresse": selection.address = true
            default: return nil
            }
        }
        return selection
    }

    var keys: [CNKeyDescriptor] {
        // Les clés de nom sont toujours lues : elles servent à l'affichage et à la
        // désambiguïsation. `fields.name` ne contrôle que leur exposition en sortie.
        var keys: [CNKeyDescriptor] = [
            CNContactIdentifierKey as CNKeyDescriptor,
            CNContactGivenNameKey as CNKeyDescriptor,
            CNContactFamilyNameKey as CNKeyDescriptor,
            CNContactOrganizationNameKey as CNKeyDescriptor,
        ]
        if birthday { keys.append(CNContactBirthdayKey as CNKeyDescriptor) }
        if phone { keys.append(CNContactPhoneNumbersKey as CNKeyDescriptor) }
        if email { keys.append(CNContactEmailAddressesKey as CNKeyDescriptor) }
        if address { keys.append(CNContactPostalAddressesKey as CNKeyDescriptor) }
        return keys
    }
}
