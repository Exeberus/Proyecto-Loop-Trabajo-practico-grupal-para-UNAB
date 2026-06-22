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
    nombre: "Gabriel Avila",
    email: "GabrielAvila@gmail.com",
    rating: 5.0,
    materias: ["Programación", "Inglés"],
    imagen: "/profes/profe1.jpg",
    descripcion:
      "Soy estudiante de la UNAB y doy apoyo en materias iniciales. Me gusta explicar paso a paso y ayudar a preparar parciales.",
  },
  {
    id: 2,
    nombre: "Maximo Barraza",
    email: "maxibarraza@gmail.com",
    rating: 4.9,
    materias: ["Programación", "Física"],
    imagen: "/profes/profe2.jpg",
    descripcion:
      "Doy clases de apoyo para estudiantes que necesitan reforzar conceptos y practicar ejercicios.",
  },
  {
    id: 3,
    nombre: "Tomas Tagliani",
    email: "tomas.tagliani@gmail.com",
    rating: 5.0,
    materias: ["Programación", "Inglés"],
    imagen: "/profes/profe3.jpg",
    descripcion:
      "Ayudo a estudiantes a organizar sus temas de estudio y resolver dudas antes de exámenes.",
  },
    {
    id: 4,
    nombre: "Abril Cejas",
    email: "Abril.Cejas@gmail.com",
    rating: 4.9,
    materias: ["Diseño", "Inglés"],
    imagen: "/profes/profe4.jpg",
    descripcion:
      "Ayudo a estudiantes a organizar sus temas de estudio y resolver dudas antes de exámenes.",
  },
    {
    id: 5,
    nombre: "Franco Gallardo",
    email: "GallardoFranco@gmail.com",
    rating: 4.0,
    materias: ["Física"],
    imagen: "/profes/profe5.jpg",
    descripcion:
      "Ayudo a estudiantes a organizar sus temas de estudio y resolver dudas antes de exámenes.",
  },
    {
    id: 6,
    nombre: "Lautaro Rodriguez",
    email: "LautyRodriguez@gmail.com",
    rating: 4.8,
    materias: ["Programación"],
    imagen: "/profes/profe6.jpg",
    descripcion:
      "Ayudo a estudiantes a organizar sus temas de estudio y resolver dudas antes de exámenes.",
  },
];
