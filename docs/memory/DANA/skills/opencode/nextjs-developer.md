# Next.js Developer (nextjs-developer)

**Source :** `/home/fatsio/.config/opencode/skills/nextjs-developer/SKILL.md`  \n**Domaine :** Framework — Next.js  \n**Type :** Skill technique  \n**Niveau :** Spécialisé (Niveau B)  \n

## Description

Next.js 14+ with App Router, server components, and server actions. Route handlers, middleware, API routes, streaming SSR, generateMetadata for SEO, loading.tsx/error.tsx boundaries, and Vercel deployment.

## Main capabilities

- **App Router configuration**: Sets up Next.js 14+ App Router with file-based routing
- **Server Components**: Implements server-side rendering and data fetching with React Server Components
- **Server Actions**: Uses server actions for form submissions and data mutations
- **Route handlers**: Creates API routes and middleware for request preprocessing
- **Streaming SSR**: Implements streaming server-side rendering with suspense boundaries
- **SEO optimization**: Configures generateMetadata for search engine optimization

## What it can do

- Set up Next.js projects with App Router structure
- Create server components and client components
- Implement server actions for forms and data mutations
- Define middleware for request preprocessing and authentication
- Set up streaming SSR with suspense boundaries for progressive rendering
- Configure metadata (title, description, openGraph, twitter) for SEO

## When it is useful

- Starting a new Next.js 14+ project with App Router
- Migrating from pages router to App Router
- Adding server-side data fetching to React components
- Implementing SEO metadata for server-rendered pages
- Setting up API routes and middleware in Next.js

## Practical examples

### Next.js App Router page

```javascript
import Metadata from "next/metadata";

export default function Page() {
  return <h1>Hello World</h1>;
}

export const metadata = {
  title: "My Page",
  description: "A description for SEO",
};
```

### Server Action example

```javascript
async function createAction(formData: FormData) {
  "use server";
  const data = {
    name: formData.get("name"),
    email: formData.get("email"),
  };
  await fetch("/api/users", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
```

### generateMetadata for SEO

```javascript
export const metadata = {
  title: "Product Page",
  description: "Learn about our amazing product",
  openGraph: {
    title: "Product Page",
    images: ["https://example.com/og-image.png"],
  },
};
```

## Original source path

`/home/fatsio/.config/opencode/skills/nextjs-developer/SKILL.md`

## Classification

- **Domaines :** framework, Next.js, React, SSR, SEO, App Router
- **Statut :** Spécialisé (Niveau B)
- **Références :** `frontend-patterns`, `mcp-developer`, `api-design`
- **Validé :** Oui (rapport d'analyse stratégique Niveau B)
- **Auteur :** OpenCode Analysis
