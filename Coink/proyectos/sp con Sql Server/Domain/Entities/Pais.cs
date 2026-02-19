namespace Domain.Entities
{
    public class Pais
    {
        public int Id { get; set; }
        public string Nombre { get; set; }
        public ICollection<Departamento> Departamentos { get; set; }
    }
}
