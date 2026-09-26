import { useCallback, useEffect, useRef, useState } from 'react'

// Loads data with loading / error / reload handling. `deps` re-run the loader.
export function useAsync(loader, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const alive = useRef(true)
  const run = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const data = await loader()
      if (alive.current) setState({ data, error: null, loading: false })
    } catch (e) {
      if (e?.name === 'AbortError') return
      if (alive.current) setState({ data: null, error: e, loading: false })
    }
  }, deps) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { alive.current = true; run(); return () => { alive.current = false } }, [run])
  const setData = useCallback((d) => setState((s) => ({ ...s, data: typeof d === 'function' ? d(s.data) : d })), [])
  return { ...state, reload: run, setData }
}
