// Shared by texel_light.gdshader / pixel_sprite.gdshader (owner: render-camera).
// Moves the lighting sample point to the centre of the texel this fragment belongs to, so 2D lights are
// evaluated once per texel (k x k block) instead of once per screen pixel. Call from fragment().
vec2 texel_light_vertex(vec2 uv, vec2 texture_pixel_size, vec2 vertex, vec2 light_vertex) {
	vec2 tex_px = uv / texture_pixel_size;
	vec2 d_tex = (floor(tex_px) + 0.5) - tex_px;            // offset to the texel centre, in texels
	mat2 j_tex = mat2(dFdx(tex_px), dFdy(tex_px));          // texels per screen pixel
	mat2 j_vtx = mat2(dFdx(vertex), dFdy(vertex));          // light-space units per screen pixel
	float det = determinant(j_tex);
	if (abs(det) > 1e-9) {
		return light_vertex + j_vtx * (inverse(j_tex) * d_tex);
	}
	return light_vertex;
}
