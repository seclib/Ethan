import { useOverlayStore } from "@/store/overlay.store";

describe("Overlay store — pile ESC centralisée", () => {
  beforeEach(() => {
    // État propre entre chaque test
    useOverlayStore.setState({ stack: [] });
  });

  it("closeTop ferme uniquement la couche la plus haute", () => {
    const bottom = jest.fn();
    const top = jest.fn();
    const un1 = useOverlayStore.getState().push({ id: "dialog-1", onClose: bottom });
    const un2 = useOverlayStore.getState().push({ id: "dialog-2", onClose: top });

    useOverlayStore.getState().closeTop();
    expect(top).toHaveBeenCalledTimes(1);
    expect(bottom).not.toHaveBeenCalled();

    un1();
    un2();
  });

  it("LIFO : plusieurs closeTop ferment du plus récent au plus ancien", () => {
    const order: string[] = [];
    const un1 = useOverlayStore.getState().push({ id: "a", onClose: () => order.push("a") });
    const un2 = useOverlayStore.getState().push({ id: "b", onClose: () => order.push("b") });
    const un3 = useOverlayStore.getState().push({ id: "c", onClose: () => order.push("c") });

    useOverlayStore.getState().closeTop();
    useOverlayStore.getState().closeTop();
    useOverlayStore.getState().closeTop();

    expect(order).toEqual(["c", "b", "a"]);
    un1();
    un2();
    un3();
  });

  it("remove retire une couche sans déclencher son onClose", () => {
    const onClose = jest.fn();
    const un = useOverlayStore.getState().push({ id: "x", onClose });

    useOverlayStore.getState().remove("x");
    useOverlayStore.getState().closeTop();

    expect(onClose).not.toHaveBeenCalled();
    expect(useOverlayStore.getState().stack).toHaveLength(0);
    un();
  });

  it("la désinscription (cleanup) retire la couche de la pile", () => {
    const onClose = jest.fn();
    const un = useOverlayStore.getState().push({ id: "y", onClose });

    un();
    expect(useOverlayStore.getState().stack).toHaveLength(0);
  });

  it("push répété avec le même id est idempotent (pas de doublon)", () => {
    const onClose = jest.fn();
    useOverlayStore.getState().push({ id: "same", onClose });
    useOverlayStore.getState().push({ id: "same", onClose });

    expect(useOverlayStore.getState().stack).toHaveLength(1);
  });

  it("pile vide → closeTop sans effet", () => {
    expect(() => useOverlayStore.getState().closeTop()).not.toThrow();
  });
});