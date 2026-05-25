method TestArrayElements(a:array<int>, j: nat)
  requires 0<=j < a.Length
  modifies a
  ensures a[j] == 60
{
  a[j] := 60;
}