import * as React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { SkillDialog } from "../../../src/components/features/skills/components/skill-dialog";

const noop = () => {};

function renderDialog(overrides: Partial<Parameters<typeof SkillDialog>[0]> = {}) {
  const state: {
    name: string;
    description: string;
    content: string;
    tags: string;
    kind: "prompt" | "pipeline";
    requiredTools: string;
    valves: string;
    saved: boolean;
  } = {
    name: "ma-skill",
    description: "",
    content: "Fais X.",
    tags: "sec,recon",
    kind: "prompt",
    requiredTools: "",
    valves: "",
    saved: false,
  };
  const props = {
    open: true,
    editingSkill: null,
    isCreating: false,
    formName: state.name,
    formDescription: state.description,
    formContent: state.content,
    formTags: state.tags,
    formKind: state.kind,
    formRequiredTools: state.requiredTools,
    formValves: state.valves,
    setFormName: (v: string) => void (state.name = v),
    setFormDescription: (v: string) => void (state.description = v),
    setFormContent: (v: string) => void (state.content = v),
    setFormTags: (v: string) => void (state.tags = v),
    setFormKind: (v: "prompt" | "pipeline") => void (state.kind = v),
    setFormRequiredTools: (v: string) => void (state.requiredTools = v),
    setFormValves: (v: string) => void (state.valves = v),
    onClose: noop,
    onSave: () => void (state.saved = true),
    ...overrides,
  };
  return { state, props };
}

/** Wrapper contrôlé : le state appartient au parent (comme dans le workspace). */
function Harness({ initialKind = "prompt" }: { initialKind?: "prompt" | "pipeline" }) {
  const [kind, setKind] = React.useState<"prompt" | "pipeline">(initialKind);
  const [name, setName] = React.useState("ma-skill");
  return (
    <SkillDialog
      open
      editingSkill={null}
      isCreating={false}
      formName={name}
      formDescription=""
      formContent="Fais X."
      formTags=""
      formKind={kind}
      formRequiredTools=""
      formValves=""
      setFormName={setName}
      setFormDescription={noop}
      setFormContent={noop}
      setFormTags={noop}
      setFormKind={setKind}
      setFormRequiredTools={noop}
      setFormValves={noop}
      onClose={noop}
      onSave={noop}
    />
  );
}

describe("SkillDialog", () => {
  it("affiche le titre et le sélecteur de type", () => {
    const { props } = renderDialog();
    render(<SkillDialog {...props} />);
    expect(screen.getByText("Nouveau skill")).toBeTruthy();
    expect(screen.getAllByText(/Prompt/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Pipeline/).length).toBeGreaterThan(0);
  });

  it("bascule vers Pipeline au clic souris (le contenu disparaît, les outils apparaissent)", () => {
    render(<Harness initialKind="prompt" />);
    const pipelineButton = screen
      .getAllByText(/Pipeline/)
      .find((el) => el.className.includes("font-medium"))
      ?.closest("button") as HTMLElement;
    expect(screen.getByText("Contenu / instructions")).toBeTruthy();
    fireEvent.click(pipelineButton);
    expect(screen.queryByText("Contenu / instructions")).toBeNull();
    expect(screen.getByText(/Outils requis/)).toBeTruthy();
  });

  it("n'appelle pas onSave quand le nom est vide (bouton désactivé)", () => {
    const { props } = renderDialog({ formName: "" });
    render(<SkillDialog {...props} />);
    const createButton = screen
      .getByRole("button", { name: "Créer" })
      .closest("button");
    expect((createButton as HTMLButtonElement).disabled).toBe(true);
  });

  it("affiche le champ des outils requis quand le type est pipeline", () => {
    const { props } = renderDialog({
      formKind: "pipeline",
      formRequiredTools: "web_search",
    });
    render(<SkillDialog {...props} />);
    expect(screen.getByText("Outils requis (séparés par des virgules)")).toBeTruthy();
  });

  it("retire le champ Contenu pour un skill pipeline", () => {
    const { props } = renderDialog({ formKind: "pipeline" });
    render(<SkillDialog {...props} />);
    expect(screen.queryByText("Contenu / instructions")).toBeNull();
  });
});