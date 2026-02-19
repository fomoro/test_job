namespace Core.Entities
{
    public class Municipio
    {
        public int Id { get; set; }
        public string Nombre { get; set; }
        public int DepartamentoId { get; set; }
        public Departamento Departamento { get; set; }
        public ICollection<Usuario> Usuarios { get; set; }
    }
}
