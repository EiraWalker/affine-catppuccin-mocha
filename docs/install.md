# Install, remove, and upgrade

## Support boundary

This procedure is a self-maintained reverse-proxy adaptation. It is not an official AFFiNE CSS API.
It does not use HTML injection, a server `customCss` setting, or an undocumented Theme Editor switch.
The reviewed stable target does not expose an audited arbitrary-CSS installation mechanism.

The overlay targets AFFiNE `0.27.4` with `@toeverything/theme` `1.1.23`.
A matching version number alone does not prove that a deployed build has the same CSS assets.
Confirm the exact asset path and original bytes for your deployment.

The helper reads a local source CSS file. It writes a **new** derived file:

```text
unaltered original CSS bytes + one newline byte + generated overlay bytes
```

It does not download files, configure a proxy, edit HTML, replace container files, or modify the source CSS.
The helper's version arguments are your assertions, checked against the repository lock.
Its CSS checks reject common wrong inputs. They are not a complete CSS parser, signature check, or server-version detector.

## 1. Prepare private files

1. Keep the original CSS, bundle, proxy configuration, and verification notes outside the public repository.
2. Save the current reverse-proxy configuration for comparison. Record the exact owned route so removal can preserve later unrelated changes.
3. Confirm the deployed AFFiNE release and its theme package against the compatibility lock.
4. Identify the exact main CSS URL in that deployment's HTML or browser network panel.
5. Fetch that asset directly from the unchanged upstream, not through an already themed route.
6. Require a successful response with CSS content, not a login page, redirect body, compressed archive, or error document.

This generic example uses a loopback upstream. Replace the example asset path before use.
The directory is private local state, not repository content.

```sh
mkdir -p ../private-theme
curl --fail --silent --show-error \
  -H 'Accept-Encoding: identity' \
  --output ../private-theme/original.css \
  'http://127.0.0.1:3010/assets/styles.REVIEWED_HASH.css'
python -X utf8 -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('../private-theme/original.css').read_bytes()).hexdigest())"
```

Do not paste credentials, cookies, workspace URLs, or private hostnames into public issues or commits.
Record the reviewed source SHA-256, version identities, and exact CSS path privately.
Do not treat an arbitrary file's freshly calculated hash as proof of provenance.

## 2. Build and check the overlay

From the repository root:

```sh
python -X utf8 scripts/build.py
python -X utf8 scripts/build.py --check
python -X utf8 -m unittest discover -s tests -v
```

Python 3.12 or newer is sufficient. These commands do not install packages or contact upstream services.

## 3. Create a derived bundle

Replace the checksum placeholder with the reviewed lowercase SHA-256.
Choose a new output filename. The helper will not overwrite an existing file.

```sh
python -X utf8 scripts/bundle.py \
  --source ../private-theme/original.css \
  --output ../private-theme/app-mocha.css \
  --source-sha256 REPLACE_WITH_REVIEWED_LOWERCASE_SHA256 \
  --affine-version 0.27.4 \
  --theme-version 1.1.23
```

The helper refuses:

- An output that already exists or aliases an input, including an existing hard link.
- A source checksum that does not match the explicit reviewed digest.
- An application or theme version outside the repository lock.
- Common wrong responses, invalid UTF-8, incomplete comments or strings, and unbalanced CSS delimiters.
- CSS without the required application token declarations.
- A source that already contains this theme.
- A generated overlay that differs from the current generator output.

The printed JSON contains source, overlay, and bundle hashes. Keep it private if stored with deployment information.
The helper preserves both input files. It does not deploy its output.

## 4. Adapt the existing reverse proxy

Serve the derived file only when **all** of these conditions match:

- The exact reviewed AFFiNE host.
- The exact reviewed main CSS URL path, including its current asset hash.
- The `GET` or `HEAD` request method.

All HTML, JavaScript, APIs, authentication, other methods, and unrelated sites must retain their existing routes.
Preserve your current TLS, authentication middleware, compression, and upstream proxy options.
Do not add a broad `*.css` override, response-body substitution, catch-all static directory, or HTML injection.

The following Caddy block illustrates only the routing boundary.
It is not a replacement for an existing production configuration.
Keep existing authentication or access controls before this route where required.
Replace the example asset path and private serving directory.

```caddyfile
example.invalid {
    @mocha_css {
        host example.invalid
        path /assets/styles.REVIEWED_HASH.css
        method GET HEAD
    }

    handle @mocha_css {
        root * /srv/affine-theme/active
        rewrite * /app-mocha.css
        header Cache-Control "no-store"
        file_server
    }

    handle {
        reverse_proxy 127.0.0.1:3010
    }
}
```

Place only the completed `app-mocha.css` in that private serving directory.
Keep the original CSS and other private files outside the served directory.
Use your existing proxy's configuration validation and atomic reload procedure.
Stage a replacement bundle outside the served directory before an atomic switch.

The file response must use its own length, content type, validators, and compression metadata.
Do not copy the original response's `Content-Length`, `Content-Encoding`, `ETag`, or integrity metadata onto changed bytes.
If the HTML uses an SRI `integrity` attribute for this asset, stop. This no-HTML-change route will not satisfy the original integrity hash.
A missing local bundle must fail visibly rather than serve an unrelated file or silently replace another asset.

## 5. Verify before accepting the installation

1. Fetch the public CSS URL and compare the response body with the local derived bundle.
2. Confirm that `HEAD` returns the corresponding headers without a response body.
3. Confirm that another host, CSS path, and non-`GET`/`HEAD` method do not receive the bundle.
4. Confirm that HTML and JavaScript responses still come from the original upstream.
5. Check authentication, document loading, and basic editing without exposing private content.
6. Compare the response's original prefix and theme suffix with the two input files byte for byte.
7. Check Light, Dark, and System appearance settings without changing the theme's scope.
8. Check text, placeholders, filled buttons, menus, dialogs, selection, and keyboard focus.
9. Check a narrow browser viewport, but do not call that a native-mobile test.
10. Check an authorized document's fonts, widths, explicit highlights, and whiteboard content palettes.
11. Check print preview and forced-colors emulation. Neither mode should activate this overlay.
12. Exercise removal and reapplication before keeping the route enabled.

The only priority exception is `color-scheme: dark !important`.
It overrides next-themes' inline native-control hint, even when the native appearance setting remains Light.
The theme does not rewrite `data-theme`, saved appearance settings, or font preferences.
The sidebar hook uses increased selector specificity instead of important paint rules.

UI colors remain Mocha under Light, Dark, and System settings.
Content palettes still follow the native appearance or the independent whiteboard appearance.
Explicit author colors and Shiki syntax colors are not overridden.
For dark-code reading, use native Dark appearance. Native Light keeps upstream `light-plus` syntax colors.
The overlay does not recalculate those colors against Mocha backgrounds.
It does not promise that all whiteboard colors follow CSS overrides or that arbitrary authored highlights meet contrast targets.

Offline tests do not perform these browser or proxy checks.
They do not validate every possible document, plugin, native application, or mobile device.

## Remove or roll back

1. Read the current proxy configuration and remove only the exact, unchanged CSS override route. Stop for inspection if it was externally edited; do not restore a stale whole-gateway backup over later unrelated changes.
2. Validate and reload the proxy through its normal procedure.
3. Confirm that the CSS URL again returns the unchanged upstream CSS.
4. Confirm that HTML, APIs, and authentication still work.
5. Refresh clients and clear affected browser, service-worker, or intermediary asset caches if necessary.
6. Remove the local derived file only after no route references it.

No database migration or document rewrite is required.
The procedure did not modify the original source CSS, HTML, or application container.
A screenshot or local test result alone does not prove that every client cache has refreshed.

## Upgrade

1. Disable the old override before changing the application version or build.
2. Confirm that the old path no longer returns the derived bundle.
3. Obtain an overlay release reviewed against the new upstream source and token set.
4. Fetch the new build's unthemed main CSS and record its new exact path and checksum.
5. Repeat the offline checks and create a new bundle from that original CSS.
6. Enable only the new exact host/path/method match.
7. Repeat the proxy, browser, print, and content-boundary checks.

Do not widen the path matcher to make an upgrade appear compatible.
Do not bypass the version guard by changing only version strings in the lock.
Unknown or changed asset paths must remain unthemed until reviewed.
Remove stale override routes. Keep old private backups only for deliberate rollback.

## Printing and accessibility boundaries

The overlay is limited to screen media while forced colors are inactive.
Print colors, pagination, fonts, and exports follow AFFiNE's own styles.
No new print reset or export transformation is supplied.
Forced-colors rendering follows the browser and upstream application.

The contrast suite calculates WCAG relative luminance for declared foreground/background pairs.
It also composites hover overlays and 0.9-opacity button labels and fills against neutral parent surfaces.
The suite checks 0.9 fill alpha separately, without fading the label.
Focus indicators use the separate 3:1 non-text contrast threshold.
It is not a complete WCAG conformance audit or a guarantee for arbitrary user colors.
Secondary text is not promised to meet 4.5:1 on Surface1 or Surface2 border/control colors.

## Versioned source references

- [Historical self-host schema](https://github.com/toeverything/AFFiNE/blob/b4c8548c09da21b2898443559a5b846f0ccf5dd8/.docker/selfhost/schema.json)
- [Stable Theme Editor flag](https://github.com/toeverything/AFFiNE/blob/b4c8548c09da21b2898443559a5b846f0ccf5dd8/packages/frontend/core/src/modules/feature-flag/constant.ts)
- [Non-configurable flag behavior](https://github.com/toeverything/AFFiNE/blob/b4c8548c09da21b2898443559a5b846f0ccf5dd8/packages/frontend/core/src/modules/feature-flag/entities/flags.ts)
- [Theme appearance selectors](https://github.com/toeverything/design/blob/8851de3927b48eeb23ae374360ca0f97b11cd93b/packages/theme/src/index.css.ts)
- [Component button variants and hover layer](https://github.com/toeverything/AFFiNE/blob/b4c8548c09da21b2898443559a5b846f0ccf5dd8/packages/frontend/component/src/ui/button/button.css.ts)
