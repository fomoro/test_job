namespace Domain.Entities
{
    public class Usuario
    {
        public int Id { get; set; }
        public string Nombre { get; set; }
        public string Telefono { get; set; }
        public string Direccion { get; set; }
        public int MunicipioId { get; set; }
        public Municipio Municipio { get; set; }
    }
}
