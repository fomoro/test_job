-- Insertar Usuario
CREATE PROCEDURE sp_InsertUsuario
    @Nombre NVARCHAR(100),
    @Telefono NVARCHAR(20),
    @Direccion NVARCHAR(200),
    @MunicipioId INT
AS
BEGIN
    INSERT INTO Usuarios (Nombre, Telefono, Direccion, MunicipioId)
    VALUES (@Nombre, @Telefono, @Direccion, @MunicipioId);

    SELECT SCOPE_IDENTITY() AS Id;
END;


-- Consultar Usuario por ID
CREATE PROCEDURE sp_GetUsuarioById
    @Id INT
AS
BEGIN
    SELECT U.Id, U.Nombre, U.Telefono, U.Direccion, U.MunicipioId, M.Nombre AS Municipio
    FROM Usuarios U
    INNER JOIN Municipios M ON U.MunicipioId = M.Id
    WHERE U.Id = @Id;
END;
