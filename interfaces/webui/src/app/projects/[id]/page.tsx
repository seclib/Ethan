/**
 * ETHAN WebUI — Project workspace page (/projects/[id])
 *
 * Cockpit d'un Project : instructions, fichiers, conversations et
 * configuration d'exécution. Toute la logique vit dans le Core ; cette page
 * ne fait que rendre le composant de feature.
 */

"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import { ProjectWorkspace } from "@/components/features/projects/project-workspace";

export default function ProjectWorkspacePage() {
	const params = useParams();
	const projectId = params.id as string;

	return <ProjectWorkspace projectId={projectId} />;
}
