type AppHeaderProps = { connected: boolean; message: string };

export default function AppHeader({ connected, message }: AppHeaderProps) {
  return <header className="topbar">
    <a className="brand" href="#"><span className="mark">N</span><span><b>Núcleo</b><small>Inteligencia comercial</small></span></a>
    <span className="connection"><i className={connected ? 'dot online' : 'dot'} />{message}</span>
    <button className="button quiet" onClick={() => window.location.reload()}>Actualizar</button>
  </header>;
}
