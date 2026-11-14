import { beforeEach, describe, expect, it } from "vitest";
import {
  cartAdd,
  cartClear,
  cartRemove,
  cartSetQty,
  getCartItems,
} from "./cart";

const rose = {
  slug: "rose-di-roma",
  name: "Roses of Rome",
  priceCents: 4900,
  image: "/x.jpg",
};
const spring = {
  slug: "primavera-romana",
  name: "Roman Spring",
  priceCents: 3900,
  image: "/y.jpg",
};

describe("cart store (order flow)", () => {
  beforeEach(() => cartClear());

  it("adds an item", () => {
    cartAdd(rose);
    expect(getCartItems()).toEqual([{ ...rose, qty: 1 }]);
  });

  it("increments quantity when the same slug is added again", () => {
    cartAdd(rose);
    cartAdd(rose, 2);
    expect(getCartItems()[0].qty).toBe(3);
  });

  it("keeps distinct items separate", () => {
    cartAdd(rose);
    cartAdd(spring);
    expect(getCartItems().map((i) => i.slug)).toEqual([
      "rose-di-roma",
      "primavera-romana",
    ]);
  });

  it("setQty to 0 removes the item", () => {
    cartAdd(rose);
    cartSetQty("rose-di-roma", 0);
    expect(getCartItems()).toEqual([]);
  });

  it("removes a single item", () => {
    cartAdd(rose);
    cartAdd(spring);
    cartRemove("rose-di-roma");
    expect(getCartItems().map((i) => i.slug)).toEqual(["primavera-romana"]);
  });

  it("computes a correct total after changes", () => {
    cartAdd(rose, 2); // 9800
    cartAdd(spring); // 3900
    const total = getCartItems().reduce(
      (n, i) => n + i.priceCents * i.qty,
      0,
    );
    expect(total).toBe(13700);
  });
});
