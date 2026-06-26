import express from "express";
import cors from "cors";
import dataRoutes from "./routes/getDataRoutes.js";
const app = express();
app.use(cors());
app.use(express.json());

let currentData = {
  speed: 42,
  rpm: 2100,
  trip_active: true,
  distance_miles: 3.2,
};

app.get("/status", (req, res) => {
  res.json(currentData);
});

app.use("/api/data", dataRoutes);

app.listen(5000, "0.0.0.0", () => {
  console.log("DashBuddy API running on port 5000");
});
