namespace Core.Entities
{
    public class Departamento
    {
        public int Id { get; set; }
        public string Nombre { get; set; }
        public int PaisId { get; set; }
        public Pais Pais { get; set; }
        public ICollection<Municipio> Municipios { get; set; }
    }
}
