using Core.Entities;

public class Pais
{
    public int Id { get; set; }
    public string Nombre { get; set; }

    // Relación con Departamento
    public ICollection<Departamento> Departamentos { get; set; }
}