method minArray(a: array<int>) returns (r:int)
  requires a.Length > 0
  ensures forall i :: 0 <= i < a.Length ==> r <= a[i]
  ensures exists i :: 0 <= i < a.Length && r == a[i]
{
  r:=a[0];
  var i:=1;
  while i<a.Length
    invariant 0 <= i <= a.Length
    invariant forall x :: 0 <= x < i ==> r <= a[x]
    invariant exists x :: 0 <= x < i && r == a[x]
    invariant forall x :: 0 <= x < a.Length ==> r <= a[x] || x >= i
  {
    if r>a[i]{
      r:=a[i];
    } else {
      r:=r;
    }
    i:=i+1;
  }
}