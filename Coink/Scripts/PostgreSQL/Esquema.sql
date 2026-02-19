CREATE TABLE Paises (
    Id SERIAL PRIMARY KEY,
    Nombre VARCHAR(100) NOT NULL
);

CREATE TABLE Departamentos (
    Id SERIAL PRIMARY KEY,
    Nombre VARCHAR(100) NOT NULL,
    PaisId INTEGER NOT NULL REFERENCES Paises(Id)
);

CREATE TABLE Municipios (
    Id SERIAL PRIMARY KEY,
    Nombre VARCHAR(100) NOT NULL,
    DepartamentoId INTEGER NOT NULL REFERENCES Departamentos(Id)
);

CREATE TABLE Usuarios (
    Id SERIAL PRIMARY KEY,
    Nombre VARCHAR(100) NOT NULL,
    Telefono VARCHAR(20) NOT NULL,
    Direccion VARCHAR(200) NOT NULL,
    MunicipioId INTEGER NOT NULL REFERENCES Municipios(Id)
);
