export default function Header() {
  return (
    <header className="site-header">
      <a className="brand" href="#top" aria-label="NICE Diabetes Evidence Assistant home">
        <span className="brand-mark" aria-hidden="true">+</span>
        <span>NICE <strong>Evidence</strong></span>
      </a>
      <div className="scope-pill"><span className="pulse" />Adult Type 1 &amp; Type 2 Diabetes</div>
    </header>
  )
}
