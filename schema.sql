-- For initial initialization
DROP TABLE IF EXISTS MonthlySummary;
DROP TABLE IF EXISTS Budget;
DROP TABLE IF EXISTS PaymentMethod;
DROP TABLE IF EXISTS ExpenseItem;
DROP TABLE IF EXISTS Category;
DROP TABLE IF EXISTS User;

-- User table
CREATE TABLE User
(
    UserID    INTEGER PRIMARY KEY AUTOINCREMENT,
    Password  TEXT        NOT NULL,
    FirstName TEXT        NOT NULL,
    LastName  TEXT        NOT NULL,
    Email     TEXT UNIQUE NOT NULL
);

-- Category table
CREATE TABLE Category
(
    CategoryID   INTEGER PRIMARY KEY AUTOINCREMENT,
    CategoryName TEXT UNIQUE NOT NULL
);

-- ExpenseItem table
CREATE TABLE ExpenseItem
(
    ExpenseID  INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID     INTEGER NOT NULL,
    Item       TEXT    NOT NULL,
    Amount     REAL    NOT NULL,
    Date       DATE    NOT NULL,
    CategoryID INTEGER NOT NULL,
    FOREIGN KEY (UserID) REFERENCES User (UserID),
    FOREIGN KEY (CategoryID) REFERENCES Category (CategoryID)
);

-- PaymentMethod table
CREATE TABLE PaymentMethod
(
    PaymentMethodID   INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID            INTEGER NOT NULL,
    PaymentMethodName TEXT    NOT NULL,
    FOREIGN KEY (UserID) REFERENCES User (UserID)
);

-- Budget table
CREATE TABLE Budget
(
    BudgetID     INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID       INTEGER NOT NULL,
    CategoryID   INTEGER NOT NULL,
    Month        TEXT    NOT NULL,
    BudgetAmount REAL    NOT NULL,
    FOREIGN KEY (UserID) REFERENCES User (UserID),
    FOREIGN KEY (CategoryID) REFERENCES Category (CategoryID)
);

-- MonthlySummary table
CREATE TABLE MonthlySummary
(
    SummaryID   INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID      INTEGER NOT NULL,
    Month       TEXT    NOT NULL,
    TotalAmount REAL    NOT NULL,
    FOREIGN KEY (UserID) REFERENCES User (UserID)
);