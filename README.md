I am not the creator of this addon, I only adapted it to work with Blender 4.0+. Here is the author and a link to the original version.

https://render.otoy.com/forum/viewtopic.php?f=32&t=82741&sid=880534359f1807a32df3b71936f05cdb

List of improvements made by me:

Here's the list of nodes converted from Cycles to Octane:

1. ShaderNodeHueSaturation (converted to OctaneColorCorrection)
2. ShaderNodeBrightContrast (converted to OctaneColorCorrection)
3. ShaderNodeRGB (converted to OctaneRGBColor)
4. ShaderNodeBsdfPrincipled (converted to OctaneUniversalMaterial)
5. ShaderNodeMapping (converted to Octane3DTransformation)
6. ShaderNodeOutputMaterial (converted to ShaderNodeOutputMaterial)
7. ShaderNodeTexImage (converted to OctaneRGBImage)
8. ShaderNodeValToRGB (converted to OctaneGradientMap)
9. ShaderNodeMix (converted to OctaneCyclesMixColorNodeWrapper)
10. ShaderNodeBsdfTranslucent (converted to OctaneUniversalMaterial with OctaneRGB Color wich mimic translucent in Octane)
11. ShaderNodeInvert (converted to OctaneInvertTexture)
12. ShaderNodeBsdfTransparent (converted to OctaneNullMaterial)
13. ShaderNodeAddShader (converted to OctaneMixMaterial)
14. ShaderNodeMixShader (converted to OctaneMixMaterial)
15. ShaderNodeMapRange (converted to OctaneOperatorRange)
16. ShaderNodeMath (converted to OctaneCyclesNodeMathNodeWrapper)
17. ShaderNodeVectorMath (converted to OctaneCyclesNodeVectorMathNodeWrapper)
18. ShaderNodeTexNoise (converted to OctaneCinema4DNoise)
19. ShaderNodeGamma (converted to OctaneColorCorrection)
20. ShaderNodeBump (converted to null node group which mimic bump node)
21. ShaderNodeNormalMap (converted to null node group which mimic normal map node)
22. ShaderNodeDisplacement (converted to OctaneTextureDisplacement)
23. ShaderNodeEmission (converted to OctaneTextureEmission)
24. ShaderNodeBlackbody (converted to OctaneBlackBodyEmission)

All nodes are compatible with Blender 4.2. Earlier versions have several incompatibilities when it comes to sockets(such as Principled BSDF or Material Output)for this reason this converter will not work on older versions of Blender.With my corrections, any convertible node values should be correctly transferred during Octane conversion. I removed the reverse conversion, which after my corrections began to whirr and generate a mass of errors 


