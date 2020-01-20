## HMF

HMF for higher rank polymorphisms.

Use `python repl.py` to experiment with the interactive type inference.

## HMF AJI

However, I finally think this is not what I want, the annotation is verbose and weak.
 
The reason why:
**I have to write this**:
```OCaml
check HMF> let f = fun (g: some a. forall b. b -> a -> a) -> fun (b: forall b.b) -> fun a -> g b a
in f
forall a0. (forall a1. (a1 -> (a0 -> a0)) -> (forall a2. a2 -> (a0 -> a0)))
```

**Instead of only specifying annotation in top level**:
```OCaml
check HMF> let f: forall a. (forall b. b -> a -> a) -> forall b. b -> a -> a = fun g -> fun a -> fun b -> g b a in f
> Exception: cannot unify types forall a0. (a0 -> (gen<a1 -> gen<a1)) (^a2 -> (^a3 -> ^a4))
```