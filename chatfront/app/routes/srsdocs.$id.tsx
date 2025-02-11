export async function loader({ request, params }: LoaderFunctionArgs) {
  try {
    const user = await requireUser(request);
    
    if (!user.group_name) {
      throw new Response("User group not found", { status: 403 });
    }

    const doc = await getDocument(params.id || '');
    
    if (!doc) {
      throw new Response("Document not found", { status: 404 });
    }

    // Process the content to find and convert PlantUML diagrams
    const content = await processPlantUml(doc.content);

    return json(
      { doc: { ...doc, content } },
      {
        headers: {
          'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0',
        },
      }
    );
  } catch (error) {
    // Redirect to login if authentication fails
    if (error instanceof Response && error.status === 401) {
      return redirect(`/login?redirectTo=/srsdocs/${params.id}`);
    }
    throw error;
  }
} 