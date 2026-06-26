import express from "express";
import { getData } from "../controllers/getDataController.js";
import { submitData } from "../controllers/getDataController.js";

const router = express.Router();

// This path is relative to where the router is mounted in server.js
router.get("/getData", getData);
router.post("/submitData", submitData);

export default router;
