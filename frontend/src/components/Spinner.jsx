export default function Spinner({ full }) {
  if (full) {
    return (
      <div className="center">
        <div className="spinner" />
      </div>
    );
  }
  return <div className="spinner" />;
}
