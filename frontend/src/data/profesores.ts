export type Profesor = {
  id: number;
  nombre: string;
  email: string;
  rating: number;
  materias: string[];
  imagen: string;
  descripcion: string;
  disponibilidad?: {
    dia: string;
    horarios: string[];
  }[];
};

export const profesores: Profesor[] = [
  {
    id: 1001,
    nombre: "Gabriel Avila",
    email: "GabrielAvila@gmail.com",
    rating: 5.0,
    materias: ["Programación", "Inglés"],
    imagen: "/profes/profe1.jpg",
    descripcion:
      "Soy estudiante de la UNAB y doy apoyo en materias iniciales. Me gusta explicar paso a paso y ayudar a preparar parciales.",
    disponibilidad: [
      { dia: "Lunes", horarios: ["15:30", "16:00", "17:00"] },
      { dia: "Miércoles", horarios: ["16:30", "18:00"] },
      { dia: "Viernes", horarios: ["15:00", "17:30"] },
    ],
  },
  {
    id: 1002,
    nombre: "Maximo Barraza",
    email: "maxibarraza@gmail.com",
    rating: 4.9,
    materias: ["Programación", "Física"],
    imagen: "/profes/profe2.jpg",
    descripcion:
      "Doy clases de apoyo para estudiantes que necesitan reforzar conceptos y practicar ejercicios.",
    disponibilidad: [
      { dia: "Martes", horarios: ["15:30", "16:30", "17:30"] },
      { dia: "Jueves", horarios: ["16:00", "17:00", "18:00"] },
    ],
  },
  {
    id: 1003,
    nombre: "Tomas Tagliani",
    email: "tomas.tagliani@gmail.com",
    rating: 5.0,
    materias: ["Programación", "Inglés"],
    imagen: "/profes/profe3.jpg",
    descripcion:
      "Ayudo a estudiantes a organizar sus temas de estudio y resolver dudas antes de exámenes.",
    disponibilidad: [
      { dia: "Lunes", horarios: ["15:00", "16:00"] },
      { dia: "Jueves", horarios: ["16:30", "17:00", "17:30"] },
    ],
  },
    {
    id: 1004,
    nombre: "Abril Cejas",
    email: "Abril.Cejas@gmail.com",
    rating: 4.9,
    materias: ["Diseño", "Inglés"],
    imagen: "/profes/profe4.jpg",
    descripcion:
      "Ayudo a estudiantes a organizar sus temas de estudio y resolver dudas antes de exámenes.",
    disponibilidad: [
      { dia: "Martes", horarios: ["15:00", "16:00", "18:00"] },
      { dia: "Sábado", horarios: ["10:00", "11:00"] },
    ],
  },
    {
    id: 1005,
    nombre: "Franco Gallardo",
    email: "GallardoFranco@gmail.com",
    rating: 4.0,
    materias: ["Física"],
    imagen: "/profes/profe5.jpg",
    descripcion:
      "Ayudo a estudiantes a organizar sus temas de estudio y resolver dudas antes de exámenes.",
    disponibilidad: [
      { dia: "Miércoles", horarios: ["15:30", "16:30"] },
      { dia: "Viernes", horarios: ["16:00", "17:00"] },
    ],
  },
    {
    id: 1006,
    nombre: "Lautaro Rodriguez",
    email: "LautyRodriguez@gmail.com",
    rating: 4.8,
    materias: ["Programación"],
    imagen: "/profes/profe6.jpg",
    descripcion:
      "Ayudo a estudiantes a organizar sus temas de estudio y resolver dudas antes de exámenes.",
    disponibilidad: [
      { dia: "Lunes", horarios: ["18:00", "19:00"] },
      { dia: "Jueves", horarios: ["15:30", "16:30", "17:30"] },
    ],
  },
];
