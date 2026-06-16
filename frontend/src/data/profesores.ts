export type Profesor = {
  id: number;
  nombre: string;
  email: string;
  rating: number;
  materias: string[];
  imagen: string;
  descripcion: string;
};

export const profesores: Profesor[] = [
  {
    id: 1,
    nombre: "Chivu Patines",
    email: "chivu.patines@gmail.com",
    rating: 4.5,
    materias: ["Matemática", "Programación"],
    imagen:
      "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=600&auto=format&fit=crop",
    descripcion:
      "Soy estudiante de la UNAB y doy apoyo en materias iniciales. Me gusta explicar paso a paso y ayudar a preparar parciales.",
  },
  {
    id: 2,
    nombre: "Profesor 2",
    email: "profe2.loop@gmail.com",
    rating: 4.5,
    materias: ["Matemática", "Programación"],
    imagen:
      "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?q=80&w=600&auto=format&fit=crop",
    descripcion:
      "Doy clases de apoyo para estudiantes que necesitan reforzar conceptos y practicar ejercicios.",
  },
  {
    id: 3,
    nombre: "Nombre Apellido",
    email: "profe3.loop@gmail.com",
    rating: 4.5,
    materias: ["Matemática", "Programación"],
    imagen:
      "https://images.unsplash.com/photo-1519345182560-3f2917c472ef?q=80&w=600&auto=format&fit=crop",
    descripcion:
      "Ayudo a estudiantes a organizar sus temas de estudio y resolver dudas antes de exámenes.",
  },
    {
    id: 4,
    nombre: "Nombre Apellido",
    email: "profe3.loop@gmail.com",
    rating: 4.5,
    materias: ["Matemática", "Programación"],
    imagen:
      "https://images.unsplash.com/photo-1519345182560-3f2917c472ef?q=80&w=600&auto=format&fit=crop",
    descripcion:
      "Ayudo a estudiantes a organizar sus temas de estudio y resolver dudas antes de exámenes.",
  },
    {
    id: 5,
    nombre: "Nombre Apellido",
    email: "profe3.loop@gmail.com",
    rating: 4.5,
    materias: ["Matemática", "Programación"],
    imagen:
      "https://images.unsplash.com/photo-1519345182560-3f2917c472ef?q=80&w=600&auto=format&fit=crop",
    descripcion:
      "Ayudo a estudiantes a organizar sus temas de estudio y resolver dudas antes de exámenes.",
  },
    {
    id: 6,
    nombre: "Nombre Apellido",
    email: "profe3.loop@gmail.com",
    rating: 4.5,
    materias: ["Matemática", "Programación"],
    imagen:
      "https://images.unsplash.com/photo-1519345182560-3f2917c472ef?q=80&w=600&auto=format&fit=crop",
    descripcion:
      "Ayudo a estudiantes a organizar sus temas de estudio y resolver dudas antes de exámenes.",
  },
];