import fs from "fs/promises";
import path from "path";

const DATA_DIR = path.join(process.cwd(), "data");
const TRIPS_FILE = path.join(DATA_DIR, "trips.json");

export const getData = async (req, res) => {
  try {
    console.log("Hi from GetDataController");
    res.status(200).json({ message: "success" });
  } catch (err) {
    console.error("Error:", err);

    res.status(500).json({
      error: "Error",
    });
  }
};

export const submitData = async (req, res) => {
  try {
    const tripData = req.body;

    await fs.mkdir(DATA_DIR, { recursive: true });

    let trips = [];

    try {
      const existing = await fs.readFile(TRIPS_FILE, "utf8");
      trips = JSON.parse(existing);
    } catch {
      trips = [];
    }

    trips.push({
      id: Date.now(),
      saved_at: new Date().toLocaleString(),
      saved_at_iso: new Date().toISOString(),
      ...tripData,
    });

    await fs.writeFile(TRIPS_FILE, JSON.stringify(trips, null, 2));

    res.status(200).json({ message: "success" });
  } catch (err) {
    console.error("Error:", err);
    res.status(500).json({ error: "Error" });
  }
};
