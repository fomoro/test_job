CREATE TABLE Paises (
    Id INT PRIMARY KEY IDENTITY(1,1),
    Nombre NVARCHAR(100) NOT NULL
);

CREATE TABLE Departamentos (
    Id INT PRIMARY KEY IDENTITY(1,1),
    Nombre NVARCHAR(100) NOT NULL,
    PaisId INT FOREIGN KEY REFERENCES Paises(Id)
);

CREATE TABLE Municipios (
    Id INT PRIMARY KEY IDENTITY(1,1),
    Nombre NVARCHAR(100) NOT NULL,
    DepartamentoId INT FOREIGN KEY REFERENCES Departamentos(Id)
);

CREATE TABLE Usuarios (
    Id INT PRIMARY KEY IDENTITY(1,1),
    Nombre NVARCHAR(100) NOT NULL,
    Telefono NVARCHAR(20) NOT NULL,
    Direccion NVARCHAR(200) NOT NULL,
    MunicipioId INT FOREIGN KEY REFERENCES Municipios(Id)
);
