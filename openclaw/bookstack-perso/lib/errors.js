export class ConfigError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
  }
}

export class BookStackError extends Error {
  constructor(code, message, status, details) {
    super(message);
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

export class ExtractError extends Error {
  constructor(code, message, details) {
    super(message);
    this.code = code;
    this.details = details;
  }
}
