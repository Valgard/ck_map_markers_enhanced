using System;
using System.Collections.Generic;

namespace MapMarkersEnhanced
{
    internal static class IconOrder
    {
        /// <summary>
        /// Moves every element <paramref name="isOurs"/> accepts to the end of
        /// <paramref name="list"/>, in place and stably: the other elements keep
        /// their relative order, then ours follow in theirs. Another mod's icon
        /// blocks are "not ours" and so keep their order too.
        /// </summary>
        /// <returns>How many elements now sit at a different index; 0 when the list was already partitioned.</returns>
        public static int MoveToEnd<T>(List<T> list, Func<T, bool> isOurs)
        {
            var others = new List<T>(list.Count);
            var ours = new List<T>();
            foreach (T item in list)
            {
                if (isOurs(item))
                {
                    ours.Add(item);
                }
                else
                {
                    others.Add(item);
                }
            }

            if (ours.Count == 0)
            {
                return 0;
            }

            var comparer = EqualityComparer<T>.Default;
            int moved = 0;
            for (int i = 0; i < list.Count; i++)
            {
                T next = i < others.Count ? others[i] : ours[i - others.Count];
                if (!comparer.Equals(list[i], next))
                {
                    list[i] = next;
                    moved++;
                }
            }
            return moved;
        }
    }
}
