// Big faded school logo behind the page (home / register and login). Purely decorative:
// it sits behind everything, never catches clicks and is hidden from screen readers.
export default function LogoBackdrop() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 -z-10 bg-center bg-no-repeat opacity-[0.18]"
      style={{ backgroundImage: "url('/logo.png')", backgroundSize: 'min(80vmin, 640px)' }}
    />
  );
}
