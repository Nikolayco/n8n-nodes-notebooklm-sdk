import type { ICredentialType, INodeProperties } from "n8n-workflow";

export class NotebookLmApi implements ICredentialType {
	name = "notebookLmApi";
	displayName = "NotebookLM API";
	documentationUrl =
		"https://github.com/Nikolayco/n8n-nodes-notebooklm-sdk#authentication";
	properties: INodeProperties[] = [
		{
			displayName: "Session JSON",
			name: "sessionJson",
			type: "string",
			typeOptions: { password: true, rows: 4 },
			default: "",
			required: true,
			description:
				"Session of a signed-in NotebookLM account: the contents of notebooklm-py's <code>storage_state.json</code>, " +
				"or the <code>Cookie</code> header copied from notebook.google.com. " +
				"Google rotates these cookies, so keep them fresh automatically (see the README, Authentication).",
		},
	];
}
