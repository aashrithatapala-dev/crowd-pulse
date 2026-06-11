import { initializeApp } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js";
import { getDatabase } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-database.js";

export const firebaseConfig = {
  apiKey: "AIzaSyAf3PXlQOGsiOBBSIrkycLn2SU570KhbQE",
  authDomain: "godavaripro-e7aa5.firebaseapp.com",
  databaseURL: "https://godavaripro-e7aa5-default-rtdb.firebaseio.com",
  projectId: "godavaripro-e7aa5",
  storageBucket: "godavaripro-e7aa5.firebasestorage.app",
  messagingSenderId: "386848633271",
  appId: "1:386848633271:web:cfcecdaac71843e32b7832",
  measurementId: "G-RH964Y4637",
};

export const app = initializeApp(firebaseConfig);
export const database = getDatabase(app);
