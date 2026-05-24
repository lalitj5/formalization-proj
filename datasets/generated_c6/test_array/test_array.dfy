method TestArrayElements(a:array<int>, j: nat)
  requires 0<=j < a.Length
  modifies a
  ensures a[j] == 60
  ensures forall k :: 0 <= k < a.Length && k != j ==> a[k] == old(a[k])
{
  var saved := a[j];
  a[j] := 60;
  if j + 1 < a.Length {
    a[j + 1] := a[j + 1];
  }
}