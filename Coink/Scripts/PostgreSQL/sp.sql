-- Insertar Usuario
CREATE OR REPLACE FUNCTION sp_insert_usuario(
    p_nombre VARCHAR,
    p_telefono VARCHAR,
    p_direccion VARCHAR,
    p_municipioid INTEGER
) RETURNS INTEGER AS $$
DECLARE
    new_id INTEGER;
BEGIN
    INSERT INTO Usuarios (Nombre, Telefono, Direccion, MunicipioId)
    VALUES (p_nombre, p_telefono, p_direccion, p_municipioid)
    RETURNING Id INTO new_id;

    RETURN new_id;
END;
$$ LANGUAGE plpgsql;



-- Consultar Usuario por ID
CREATE OR REPLACE FUNCTION sp_get_usuario_by_id(
    p_id INTEGER
) RETURNS TABLE (
    Id INTEGER,
    Nombre VARCHAR,
    Telefono VARCHAR,
    Direccion VARCHAR,
    MunicipioId INTEGER,
    Municipio VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT U.Id, U.Nombre, U.Telefono, U.Direccion, U.MunicipioId, M.Nombre AS Municipio
    FROM Usuarios U
    INNER JOIN Municipios M ON U.MunicipioId = M.Id
    WHERE U.Id = p_id;
END;
$$ LANGUAGE plpgsql;

