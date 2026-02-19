namespace Core.Dtos
{
    public class UsuarioCoreDto
    {
        public int Id { get; set; }
        public string Nombre { get; set; }
        public string Telefono { get; set; }
        public string Direccion { get; set; }
        public int MunicipioId { get; set; }
        public string MunicipioNombre { get; set; }
    }
}
