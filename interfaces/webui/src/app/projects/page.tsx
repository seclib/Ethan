/**
 * ETHAN WebUI — Projects page (/projects)
 *
 * Inventaire des Projects (source : ProjectManager Core). Le WebUI ne fait
 * que rendre la liste ; toute mutation délègue à /v1/projects.
 */

"use client";

import * as React from "react";
import { ProjectsList } from "@/components/features/projects/projects-list";

export default function ProjectsPage() {
	return <ProjectsList />;
}
